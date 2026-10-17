from app.ai.schema_context import build_schema_context


def test_employee_schema(monkeypatch):

    policy = {
        "employee_id": "EMP002",
        "role": "Employee",
        "tables": {
            "employees": {
                "allowed_columns": {
                    "employee_id",
                    "name",
                    "email",
                    "department_id",
                    "designation",
                    "joining_date",
                    "status",
                },
                "row_condition": None,
                "privacy": {},
            }
        },
    }

    monkeypatch.setattr(
        "app.ai.schema_context.get_user_policy",
        lambda *_: policy
    )

    schema = build_schema_context("EMP002")

    assert "employee_id" in schema
    assert "name" in schema
    assert "email" in schema

    assert "salary" not in schema
    assert "phone" not in schema
    assert "address" not in schema


def test_admin_schema(monkeypatch):

    policy = {
        "employee_id": "EMP001",
        "role": "Admin",
        "tables": {
            "employees": {
                "allowed_columns": {
                    "employee_id",
                    "name",
                    "email",
                    "phone",
                    "department_id",
                    "designation",
                    "joining_date",
                    "salary",
                    "address",
                    "status",
                },
                "row_condition": None,
                "privacy": {},
            }
        },
    }

    monkeypatch.setattr(
        "app.ai.schema_context.get_user_policy",
        lambda *_: policy
    )

    schema = build_schema_context("EMP001")

    assert "salary" in schema
    assert "phone" in schema
    assert "address" in schema


def test_no_policy(monkeypatch):

    monkeypatch.setattr(
        "app.ai.schema_context.get_user_policy",
        lambda *_: None
    )

    try:
        build_schema_context("UNKNOWN")
        assert False
    except PermissionError:
        assert True