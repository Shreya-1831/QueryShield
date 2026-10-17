from app.policy.policy_service import build_privacy_context


def test_build_privacy_context_from_database():

    context = build_privacy_context("EMP002")

    assert context is not None

    assert context.employee_id == "EMP002"
    assert context.role == "Employee"

    assert "employees" in context.allowed_columns

    assert "salary" in context.allowed_columns["employees"]
    assert "date_of_birth" in context.allowed_columns["employees"]

    salary_rule = context.privacy_rules["employees"]["salary"]

    assert salary_rule["sensitivity"] == "sensitive"
    assert salary_rule["action"] == "mask"

    dob_rule = context.privacy_rules["employees"]["date_of_birth"]

    assert dob_rule["sensitivity"] == "sensitive"
    assert dob_rule["action"] == "mask"