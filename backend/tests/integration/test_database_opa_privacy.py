from app.policy.policy_service import build_privacy_context
from app.privacy.opa_service import OPAService
from app.privacy.privacy_service import PrivacyService


def test_database_policy_to_opa_to_privacy():

    employee_id = "EMP002"

    # 1. Load policy directly from MySQL
    context = build_privacy_context(employee_id)

    assert context is not None
    assert context.role == "Employee"

    # 2. Simulate the result returned by MySQL
    rows = [
        {
            "employee_id": "EMP002",
            "name": "Priya Sharma",
            "salary": 55000,
            "date_of_birth": "2002-08-21",
        }
    ]

    table_name = "employees"

    # 3. Build OPA input from the REAL database policy
    opa_input = {
        "result_columns": list(rows[0].keys()),

        "allowed_columns": sorted(
            context.allowed_columns[table_name]
        ),

        "privacy_rules": context.privacy_rules[table_name],
    }

    # 4. Ask local OPA for the privacy decision
    opa = OPAService()

    decision = opa.evaluate(opa_input)

    # 5. Verify OPA decision
    assert decision["allowed"] is True

    assert decision["actions"]["salary"] == "mask"
    assert decision["actions"]["date_of_birth"] == "mask"

    # 6. Apply the OPA decision
    privacy = PrivacyService()

    result = privacy.protect(
        rows,
        context,
        table_name,
        decision,
    )

    # 7. Verify final protected response
    assert result.blocked is False

    assert result.rows[0]["employee_id"] == "EMP002"
    assert result.rows[0]["name"] == "Priya Sharma"

    assert result.rows[0]["salary"] != 55000
    assert result.rows[0]["date_of_birth"] != "2002-08-21"

    assert result.masked_fields == 2