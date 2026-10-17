import time
from sqlalchemy import text

from app.database.connection import settings
from app.ai.ollama_service import generate_sql
from app.ai.intent_classifier import intent_classifier
from app.ai.response_service import response_service
from app.policy.policy_service import get_user_policy, build_privacy_context
from app.security.prompt_scanner import scan_prompt
from app.security.sql_authorizer import authorize_sql, extract_query_metadata
from app.database.connection_manager import db_manager
from app.privacy.opa_service import OPAService
from app.privacy.privacy_service import PrivacyService
from app.privacy.presidio_service import PresidioService
from app.audit.audit_service import audit_service
from app.visualization.visualization_service import visualization_service
from app.security.sql_hardener import harden_sql


opa_service, privacy_service, presidio_service = OPAService(), PrivacyService(), PresidioService()


def audit(employee_id, prompt, *, intent=None, status=None, sql=None,
          authorized_sql=None, risk=None, auth=None, privacy=None,
          execution=None, rows=None, exec_ms=None, total_ms=None, event=None):
    try:
        audit_service.record_query(
            employee_id=employee_id, prompt=prompt, intent=intent,
            generated_sql=sql, status=status, risk_level=risk,
            authorized_sql=authorized_sql, authorization_decision=auth,
            privacy_decision=privacy, execution_status=execution,
            row_count=rows, execution_time_ms=exec_ms, total_time_ms=total_ms
        )
        if event:
            audit_service.record_security_event(employee_id, event[0], event[1])
    except Exception:
        pass


def execute_query(employee_id: str, prompt: str, role: str) -> dict:
    start = time.perf_counter()

    def finish(response, **kwargs):
        audit(
            employee_id,
            prompt,
            total_ms=int((time.perf_counter() - start) * 1000),
            **kwargs
        )
        return response

    # 1. Prompt security
    scan = scan_prompt(prompt)
    if not scan.allowed:
        return finish(
            {"success": False, "stage": "prompt_security", "reason": scan.reason,
             "categories": scan.categories, "risk_level": scan.risk_level.value},
            status="BLOCKED", risk=scan.risk_level.value, auth="DENIED",
            execution="NOT_EXECUTED",
            event=("PROMPT_SECURITY_BLOCK", scan.reason)
        )

    # 2. Intent classification
    intent = intent_classifier.classify(prompt)
    intent_name = intent.intent.value

    # 3. Policy
    policy = get_user_policy(employee_id)
    if not policy:
        return finish(
            {"success": False, "stage": "authorization",
             "reason": "No active policy found"},
            intent=intent_name, status="BLOCKED", auth="DENIED",
            execution="NOT_EXECUTED",
            event=("POLICY_NOT_FOUND", "No active authorization policy found.")
        )

    # 4. Role consistency
    if policy["role"] != role:
        return finish(
            {"success": False, "stage": "authorization",
             "reason": "Identity role does not match authorization policy"},
            intent=intent_name, status="BLOCKED", auth="DENIED",
            execution="NOT_EXECUTED",
            event=("ROLE_MISMATCH", "Verified role and policy role do not match.")
        )

    # 5. Broad employee request
    broad = ("all employees", "all employee", "everyone", "every employee")
    if policy["role"] == "Employee" and any(x in prompt.lower() for x in broad):
        return finish(
            {
                "success": False,
                "stage": "authorization",
                "reason": "Employees cannot request unrestricted employee data for all employees",
                "safe_alternative": "You can ask for your own employee information.",
            },
            intent=intent_name,
            status="BLOCKED",
            auth="DENIED",
            execution="NOT_EXECUTED",
            event=(
                "BROAD_DATA_REQUEST",
                "Employee requested unrestricted employee data."
            )
        )

    # 6. Authorized schema + row restriction
    allowed_tables = set(policy["tables"])
    allowed_columns = {
        table: set(data["allowed_columns"])
        for table, data in policy["tables"].items()
    }
    
    import re

    row_conditions = {}

    for table_name, table_policy in policy["tables"].items():
        condition = table_policy.get("row_condition")

        if not condition:
            continue

        if "{employee_id}" in condition:
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", employee_id):
                raise PermissionError("Invalid employee identity")

            condition = condition.replace(
                "{employee_id}",
                # f"{employee_id}",
                employee_id,
            )

        if re.search(r"\{[^}]+\}", condition):
            raise PermissionError("Unsupported row-policy placeholder")

        row_conditions[table_name] = condition


    # 7. Generate SQL
    sql = generate_sql(employee_id, prompt)

    # 8. SQL authorization
    authorized, reason, authorized_sql = authorize_sql(
        sql=sql,
        allowed_columns=allowed_columns,
        allowed_tables=allowed_tables,
        row_condition=row_conditions,
        allowed_database=settings.MYSQL_DATABASE,
    )
    if not authorized:
        return finish(
            {"success": False, "stage": "sql_authorization",
             "sql": sql, "reason": reason},
            intent=intent_name, status="BLOCKED", sql=sql,
            risk=scan.risk_level.value, auth="DENIED",
            execution="NOT_EXECUTED",
            event=("SQL_AUTHORIZATION_FAILURE", reason)
        )

    # 9. SQL hardening
    safe, reason, authorized_sql = harden_sql(authorized_sql)

    if not safe:
        return finish(
            {"success": False, "stage": "sql_hardening",
            "sql": authorized_sql, "reason": reason},
            intent=intent_name, status="BLOCKED",
            sql=sql, authorized_sql=authorized_sql,
            risk=scan.risk_level.value, auth="DENIED",
            execution="NOT_EXECUTED",
            event=("SQL_HARDENING_FAILURE", reason)
        )

    # 10. Database execution
    exec_start = time.perf_counter()
    try:
        with db_manager.connect(role) as db:
            result = db.execute(text(authorized_sql))
            rows = [dict(r) for r in result.mappings().all()]
        exec_ms = int((time.perf_counter() - exec_start) * 1000)
    except Exception as exc:
        exec_ms = int((time.perf_counter() - exec_start) * 1000)

        return finish(
            {
                "success": False,
                "stage": "database_execution",
                "sql": authorized_sql,
                "reason": f"Database execution failed: {exc}",
            },
            intent=intent_name,
            status="ERROR",
            sql=sql,
            authorized_sql=authorized_sql,
            risk=scan.risk_level.value,
            auth="ALLOWED",
            execution="FAILED",
            exec_ms=exec_ms,
            event=("DATABASE_EXECUTION_FAILURE", str(exc))
        )
    
    # 11. Empty result
    if not rows:
        return finish(
            {"success": True, "sql": authorized_sql, "row_count": 0,
             "data": [], "privacy": {"blocked": False, "leakage_detected": False}},
            intent=intent_name, status="SUCCESS", sql=sql,
            authorized_sql=authorized_sql, risk=scan.risk_level.value,
            auth="ALLOWED", privacy="ALLOWED", execution="SUCCESS",
            rows=0, exec_ms=exec_ms
        )

    # 12. Privacy context
    privacy_context = build_privacy_context(employee_id)
    if not privacy_context:
        return finish(
            {"success": False, "stage": "privacy_authorization",
             "sql": authorized_sql, "reason": "No privacy policy found"},
            intent=intent_name, status="BLOCKED", sql=sql,
            authorized_sql=authorized_sql, risk=scan.risk_level.value,
            auth="ALLOWED", privacy="DENIED", execution="COMPLETED",
            rows=len(rows), exec_ms=exec_ms,
            event=("PRIVACY_POLICY_MISSING", "No privacy policy found.")
        )

    # 13. OPA
    result_columns = list(rows[0])

    try:
        metadata = extract_query_metadata(authorized_sql,allowed_columns)

        opa_input = {
            "employee_id": employee_id,
            "role": policy["role"],
            "allowed_columns": {
                t: sorted(p["allowed_columns"])
                for t, p in policy["tables"].items()
            },
            "privacy_rules": {
                t: dict(p["privacy"])
                for t, p in policy["tables"].items()
            },
            "result_columns": result_columns,
            "physical_columns": metadata["physical_columns"],
            "derived_columns": metadata["derived_columns"],
            "filter_derivations": metadata["filter_derivations"],
        }

        opa_decision = opa_service.evaluate(opa_input)

    except Exception as exc:
        return finish(
            {
                "success": False,
                "stage": "privacy_policy",
                "sql": authorized_sql,
                "reason": f"Privacy policy evaluation failed: {exc}",
            },
            intent=intent_name,
            status="BLOCKED",
            sql=sql,
            authorized_sql=authorized_sql,
            risk=scan.risk_level.value,
            auth="ALLOWED",
            privacy="ERROR",
            execution="COMPLETED",
            rows=len(rows),
            exec_ms=exec_ms,
            event=("PRIVACY_POLICY_ERROR", str(exc)),
        )
    # 14. Privacy protection
    # table_name = next(iter(policy["tables"]))
    protected = privacy_service.protect(rows, privacy_context, None, opa_decision, authorized_sql=authorized_sql,)

    if protected.blocked:
        reason = "; ".join(protected.reasons) or "Privacy policy blocked the result"
        return finish(
            {"success": False, "stage": "privacy_authorization",
             "sql": authorized_sql, "reason": reason,
             "privacy": {
                 "blocked": True, "leakage_detected": True,
                 "masked_fields": protected.masked_fields,
                 "removed_fields": protected.removed_fields
             }},
            intent=intent_name, status="BLOCKED", sql=sql,
            authorized_sql=authorized_sql, risk=scan.risk_level.value,
            auth="ALLOWED", privacy="DENIED", execution="COMPLETED",
            rows=len(rows), exec_ms=exec_ms,
            event=("PRIVACY_BLOCK", reason)
        )

    # 15. Presidio
    final_rows = [
        {
            c: (
                presidio_service.protect_text(v)["text"]
                if isinstance(v, str)
                and any(
                    context.get("action") in {"mask", "remove"}
                    for table in policy["tables"].values()
                    for column, context in table["privacy"].items()
                    if column == c
                )
                else v
            )
            for c, v in row.items()
        }
        for row in protected.rows
    ]

    # 16. Natural-language response
    response_text = response_service.generate(
        prompt=prompt,
        rows=final_rows,
        intent=intent_name,
    )

    # 17. Visualization
    visualization = visualization_service.analyze(
        final_rows,
        title="Query Result",
    )

    # 18. Success
    return finish(
        {
            "success": True,
            "response": response_text,
            "sql": authorized_sql,
            "row_count": len(final_rows),
            "data": final_rows,
            "visualization": {
                "type": visualization.visualization_type.value,
                "title": visualization.title,
                "x_axis": visualization.x_axis,
                "y_axis": visualization.y_axis,
                "data": visualization.data,
                "reason": visualization.reason,
            },
            "privacy": {
                "blocked": False,
                "leakage_detected": protected.leakage_detected,
                "masked_fields": protected.masked_fields,
                "removed_fields": protected.removed_fields,
                "reasons": protected.reasons,
            },
        },
        intent=intent_name,
        status="SUCCESS",
        sql=sql,
        authorized_sql=authorized_sql,
        risk=scan.risk_level.value,
        auth="ALLOWED",
        privacy="ALLOWED",
        execution="SUCCESS",
        rows=len(final_rows),
        exec_ms=exec_ms,
    )