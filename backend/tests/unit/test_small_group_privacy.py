from app.privacy.privacy_service import PrivacyService


def test_small_group_aggregation_is_blocked():
    service = PrivacyService(small_group_threshold=5)

    rows = [
        {"department_id": 1, "employee_count": 10},
        {"department_id": 2, "employee_count": 2},
        {"department_id": 3, "employee_count": 8},
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
        None,
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
    assert result.rows == []
    assert "Small-group aggregation blocked" in result.reasons[0]


def test_safe_aggregation_is_allowed():
    service = PrivacyService(small_group_threshold=5)

    rows = [
        {"department_id": 1, "employee_count": 10},
        {"department_id": 2, "employee_count": 8},
        {"department_id": 3, "employee_count": 7},
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
        None,
        "employees",
        decision,
        authorized_sql="""
            SELECT department_id,
                   COUNT(employee_id) AS employee_count
            FROM employees
            GROUP BY department_id
        """,
    )

    assert result.blocked is False
    assert result.leakage_detected is False
    assert result.rows == rows


def test_non_aggregation_query_is_not_blocked():
    service = PrivacyService(small_group_threshold=5)

    rows = [
        {"department_id": 1, "name": "Alice"},
        {"department_id": 2, "name": "Bob"},
    ]

    decision = {
        "allowed": True,
        "actions": {
            "department_id": "allow",
            "name": "allow",
        },
    }

    result = service.protect(
        rows,
        None,
        "employees",
        decision,
        authorized_sql="""
            SELECT department_id, name
            FROM employees
        """,
    )

    assert result.blocked is False
    assert result.rows == rows


def test_malformed_aggregation_fails_closed():
    service = PrivacyService(small_group_threshold=5)

    rows = [
        {"department_id": 1, "employee_count": 2},
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
        None,
        "employees",
        decision,
        authorized_sql="SELECT department_id, COUNT(employee_id",
    )

    assert result.blocked is True
    assert result.leakage_detected is True
    assert "could not be safely evaluated" in result.reasons[0]
