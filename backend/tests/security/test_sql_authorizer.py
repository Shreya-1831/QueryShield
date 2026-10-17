from app.security.sql_authorizer import authorize_sql

employee_cols = {
    "employee_id", "name", "date_of_birth", "email",
    "department_id", "designation", "joining_date", "status"
}

admin_cols = {
    "employee_id", "name", "date_of_birth", "email", "phone",
    "department_id", "designation", "joining_date", "salary",
    "address", "status"
}


def test_employee_allowed():
    ok, _, _ = authorize_sql(
        "SELECT name, designation FROM employees",
        employee_cols, ["employees"]
    )
    assert ok


def test_employee_dob_allowed():
    ok, _, _ = authorize_sql(
        "SELECT name, date_of_birth FROM employees",
        employee_cols, ["employees"]
    )
    assert ok


def test_employee_salary_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name, salary FROM employees",
        employee_cols, ["employees"]
    )
    assert not ok


def test_admin_salary_allowed():
    ok, _, _ = authorize_sql(
        "SELECT name, salary FROM employees",
        admin_cols, ["employees"]
    )
    assert ok


def test_employee_select_all_blocked():
    ok, _, _ = authorize_sql(
        "SELECT * FROM employees",
        employee_cols, ["employees"]
    )
    assert not ok


def test_age_calculation_allowed():
    ok, _, sql = authorize_sql(
        "SELECT name, TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) AS age "
        "FROM employees",
        employee_cols, ["employees"]
    )
    assert ok
    assert "date_of_birth" in sql


def test_employee_row_authorization():
    ok, _, sql = authorize_sql(
        "SELECT name, date_of_birth FROM employees",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "employee_id = 'EMP002'" in sql


def test_existing_where_preserved():
    ok, _, sql = authorize_sql(
        "SELECT name FROM employees WHERE status = 'active'",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "status = 'active'" in sql
    assert "employee_id = 'EMP002'" in sql


def test_row_policy_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees",
        employee_cols, ["employees"],
        "salary > 50000"
    )
    assert not ok

def test_unauthorized_join_blocked():
    ok, _, _ = authorize_sql(
        "SELECT e.name, d.department_name "
        "FROM employees e JOIN departments d "
        "ON e.department_id = d.department_id",
        employee_cols, ["employees"]
    )
    assert not ok


def test_allowed_join():
    ok, _, _ = authorize_sql(
        "SELECT e.name, e.designation "
        "FROM employees e JOIN employees e2 "
        "ON e.employee_id = e2.employee_id",
        employee_cols, ["employees"]
    )
    assert ok


def test_unauthorized_subquery_table_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees "
        "WHERE employee_id IN "
        "(SELECT employee_id FROM users)",
        employee_cols, ["employees"]
    )
    assert not ok


def test_subquery_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees "
        "WHERE salary > (SELECT salary FROM employees)",
        employee_cols, ["employees"]
    )
    assert not ok

def test_insert_blocked():
    ok, _, _ = authorize_sql(
        "INSERT INTO employees (name) VALUES ('Hacker')",
        admin_cols, ["employees"]
    )
    assert not ok


def test_update_blocked():
    ok, _, _ = authorize_sql(
        "UPDATE employees SET name = 'Hacker'",
        admin_cols, ["employees"]
    )
    assert not ok


def test_delete_blocked():
    ok, _, _ = authorize_sql(
        "DELETE FROM employees",
        admin_cols, ["employees"]
    )
    assert not ok


def test_drop_blocked():
    ok, _, _ = authorize_sql(
        "DROP TABLE employees",
        admin_cols, ["employees"]
    )
    assert not ok


def test_multiple_statements_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees; DELETE FROM employees",
        admin_cols, ["employees"]
    )
    assert not ok


def test_sql_comment_obfuscation():
    ok, _, _ = authorize_sql(
        "SELECT name, salary FROM employees -- unauthorized",
        employee_cols, ["employees"]
    )
    assert not ok

def test_row_policy_blocks_other_employee():
    ok, _, sql = authorize_sql(
        "SELECT name, email FROM employees "
        "WHERE employee_id = 'EMP001'",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "EMP001" in sql
    assert "EMP002" in sql
    assert "AND" in sql


def test_row_policy_applied_without_where():
    ok, _, sql = authorize_sql(
        "SELECT name, email FROM employees",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "employee_id = 'EMP002'" in sql


def test_row_policy_with_or_cannot_bypass():
    ok, _, sql = authorize_sql(
        "SELECT name FROM employees "
        "WHERE employee_id = 'EMP001' OR status = 'active'",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "employee_id = 'EMP002'" in sql
    assert " OR " in sql


def test_row_policy_cannot_use_salary():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees",
        employee_cols, ["employees"],
        "salary > 50000"
    )
    assert not ok


def test_row_policy_cannot_use_unauthorized_table():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees",
        employee_cols, ["employees"],
        "department_id IN (SELECT department_id FROM departments)"
    )
    assert not ok

def test_alias_with_row_policy():
    ok, _, sql = authorize_sql(
        "SELECT e.name, e.email FROM employees e "
        "WHERE e.status = 'active'",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "employee_id = 'EMP002'" in sql


def test_alias_with_qualified_row_policy():
    ok, _, sql = authorize_sql(
        "SELECT e.name FROM employees e",
        employee_cols, ["employees"],
        "e.employee_id = 'EMP002'"
    )
    assert ok
    assert "EMP002" in sql


def test_alias_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT e.name FROM employees e",
        employee_cols, ["employees"],
        "e.salary > 50000"
    )
    assert not ok


def test_alias_unauthorized_table_blocked():
    ok, _, _ = authorize_sql(
        "SELECT e.name FROM employees e",
        employee_cols, ["employees"],
        "e.department_id IN (SELECT department_id FROM departments)"
    )
    assert not ok

def test_aggregation_allowed():
    ok, _, _ = authorize_sql(
        "SELECT department_id, COUNT(*) AS total "
        "FROM employees GROUP BY department_id",
        employee_cols, ["employees"]
    )
    assert ok


def test_aggregation_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT department_id, AVG(salary) AS avg_salary "
        "FROM employees GROUP BY department_id",
        employee_cols, ["employees"]
    )
    assert not ok


def test_having_allowed():
    ok, _, _ = authorize_sql(
        "SELECT department_id, COUNT(employee_id) AS total "
        "FROM employees GROUP BY department_id "
        "HAVING COUNT(employee_id) > 1",
        employee_cols, ["employees"]
    )
    assert ok


def test_having_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT department_id, COUNT(employee_id) AS total "
        "FROM employees GROUP BY department_id "
        "HAVING AVG(salary) > 50000",
        employee_cols, ["employees"]
    )
    assert not ok

def test_order_by_allowed_column():
    ok, _, _ = authorize_sql(
        "SELECT name, designation FROM employees ORDER BY name",
        employee_cols, ["employees"]
    )
    assert ok


def test_order_by_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name FROM employees ORDER BY salary",
        employee_cols, ["employees"]
    )
    assert not ok


def test_limit_allowed():
    ok, _, _ = authorize_sql(
        "SELECT name, designation FROM employees LIMIT 5",
        employee_cols, ["employees"]
    )
    assert ok


def test_order_by_alias_allowed():
    ok, _, _ = authorize_sql(
        "SELECT name AS employee_name FROM employees "
        "ORDER BY employee_name",
        employee_cols, ["employees"]
    )
    assert not ok


def test_expression_with_unauthorized_column_blocked():
    ok, _, _ = authorize_sql(
        "SELECT name, salary + 1000 AS adjusted_salary "
        "FROM employees",
        employee_cols, ["employees"]
    )
    assert not ok

def test_schema_qualified_table():
    ok, _, _ = authorize_sql(
        "SELECT name FROM queryshield.employees",
        employee_cols, ["employees"]
    )
    assert not ok


def test_complex_where_with_row_policy():
    ok, _, sql = authorize_sql(
        "SELECT name FROM employees "
        "WHERE status = 'active' AND designation = 'Developer'",
        employee_cols, ["employees"],
        "employee_id = 'EMP002'"
    )
    assert ok
    assert "EMP002" in sql


def test_empty_sql_blocked():
    ok, _, _ = authorize_sql(
        "", employee_cols, ["employees"]
    )
    assert not ok


def test_invalid_sql_blocked():
    ok, _, _ = authorize_sql(
        "SELECT FROM employees",
        employee_cols, ["employees"]
    )
    assert not ok


def test_whitespace_sql_blocked():
    ok, _, _ = authorize_sql(
        "   ", employee_cols, ["employees"]
    )
    assert not ok