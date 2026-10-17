from app.privacy.privacy_service import (
    PrivacyContext,
    PrivacyService,
)


def employee_privacy_context():
    return PrivacyContext(
        employee_id="EMP003",
        role="Admin",
        allowed_columns={
            "employees": {
                "department_id",
                "employee_id",
                "salary",
                "name",
            }
        },
        privacy_rules={
            "employees": {
                "department_id": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
                "employee_id": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
                "name": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
                "salary": {
                    "sensitivity": "sensitive",
                    "action": "mask",
                },
            }
        },
    )


def test_avg_sensitive_column_is_blocked():
    service = PrivacyService()

    rows = [
        {
            "department_id": 1,
            "average_salary": 65000,
        }
    ]

    decision = {
        "allowed": True,
        "actions": {
            "department_id": "allow",
            "average_salary": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_privacy_context(),
        "employees",
        decision,
        authorized_sql="""
            SELECT department_id,
                   AVG(salary) AS average_salary
            FROM employees
            GROUP BY department_id
        """,
    )

    assert result.blocked is True
    assert result.leakage_detected is True
    assert "Sensitive aggregation blocked" in result.reasons[0]


def test_sum_sensitive_column_is_blocked():
    service = PrivacyService()

    rows = [
        {
            "department_id": 1,
            "total_salary": 300000,
        }
    ]

    decision = {
        "allowed": True,
        "actions": {
            "department_id": "allow",
            "total_salary": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_privacy_context(),
        "employees",
        decision,
        authorized_sql="""
            SELECT department_id,
                   SUM(salary) AS total_salary
            FROM employees
            GROUP BY department_id
        """,
    )

    assert result.blocked is True
    assert result.leakage_detected is True
    assert "Sensitive aggregation blocked" in result.reasons[0]


def test_count_employee_id_still_uses_small_group_rule():
    service = PrivacyService(small_group_threshold=5)

    rows = [
        {
            "department_id": 1,
            "employee_count": 2,
        }
    ]

    decision = {
        "allowed": True,
        "actions": {
            "department_id": "allow",
            "employee_count": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_privacy_context(),
        "employees",
        decision,
        authorized_sql="""
            SELECT department_id,
                   COUNT(employee_id) AS employee_count
            FROM employees
            GROUP BY department_id
        """,
    )

    assert result.blocked is True
    assert result.leakage_detected is True
    assert "Small-group aggregation blocked" in result.reasons[0]