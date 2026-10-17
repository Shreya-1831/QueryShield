from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database.connection import engine
from app.identity.identity_service import identity_service


router = APIRouter(
    prefix="/api/admin/audit",
    tags=["Admin Audit"],
)


def require_admin():
    identity = identity_service.resolve()

    if not identity:
        raise HTTPException(
            status_code=401,
            detail="Windows identity could not be verified",
        )

    if identity.get("role") != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return identity


@router.get("")
def get_audit_logs(
    employee_id: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
    limit: int = 100,
):
    require_admin()

    limit = max(1, min(limit, 500))

    query = """
        SELECT
            q.query_id,
            u.employee_id,
            u.username,
            q.prompt,
            q.intent,
            q.generated_sql,
            q.authorized_sql,
            q.risk_level,
            q.authorization_decision,
            q.privacy_decision,
            q.execution_status,
            q.status,
            q.row_count,
            q.execution_time_ms,
            q.total_time_ms,
            q.created_at
        FROM query_history q
        JOIN users u
            ON q.user_id = u.user_id
    """

    conditions = []
    params = {
        "limit": limit,
    }

    if employee_id:
        conditions.append("u.employee_id = :employee_id")
        params["employee_id"] = employee_id

    if status:
        conditions.append("q.status = :status")
        params["status"] = status

    if risk_level:
        conditions.append("q.risk_level = :risk_level")
        params["risk_level"] = risk_level

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """
        ORDER BY q.created_at DESC, q.query_id DESC
        LIMIT :limit
    """

    with engine.connect() as db:
        rows = db.execute(
            text(query),
            params,
        ).mappings().all()

    return {
        "success": True,
        "count": len(rows),
        "audit_logs": [dict(row) for row in rows],
    }