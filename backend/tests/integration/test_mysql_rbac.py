from sqlalchemy import text

from app.database.connection import engine
from app.policy.policy_service import get_user_policy
from app.security.sql_authorizer import authorize_sql


def run_real_query(employee_id, sql):
    policy = get_user_policy(employee_id)
    assert policy is not None

    tables = set(policy["tables"])
    columns = {
        c
        for p in policy["tables"].values()
        for c in p["allowed_columns"]
    }

    conditions = [
        p["row_condition"]
        for p in policy["tables"].values()
        if p.get("row_condition")
    ]

    condition = conditions[0] if conditions else None

    if condition:
        condition = condition.replace(
            "{employee_id}", f"'{employee_id}'"
        )

    ok, reason, authorized_sql = authorize_sql(
        sql, columns, tables, condition
    )
    assert ok, reason

    with engine.connect() as db:
        return db.execute(text(authorized_sql)).mappings().all()


def test_employee_can_access_own_data():
    rows = run_real_query(
        "EMP002",
        "SELECT employee_id, name, salary "
        "FROM employees "
        "WHERE employee_id = 'EMP002'",
    )
    assert all(row["employee_id"] == "EMP002" for row in rows)


def test_employee_cannot_access_other_employee():
    rows = run_real_query(
        "EMP002",
        "SELECT employee_id, name, salary "
        "FROM employees "
        "WHERE employee_id = 'EMP001'",
    )
    assert rows == []


def test_admin_can_access_all_employees():
    rows = run_real_query(
        "EMP001",
        "SELECT employee_id, name, salary "
        "FROM employees",
    )
    assert len(rows) >= 2