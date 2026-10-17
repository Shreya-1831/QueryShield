from app.security.sql_authorizer import authorize_sql

columns = {"name", "email", "employee_id"}
tables = {"employees"}
row = "employee_id = 'EMP002'"

tests = [
    ("Valid", "SELECT name FROM employees"),
    ("Same employee", "SELECT name FROM employees WHERE employee_id = 'EMP002'"),
    ("Other employee", "SELECT name FROM employees WHERE employee_id = 'EMP001'"),
    ("IN bypass", "SELECT name FROM employees WHERE employee_id IN ('EMP001','EMP002')"),
    ("NOT bypass", "SELECT name FROM employees WHERE NOT employee_id = 'EMP002'"),
    ("OR bypass", "SELECT name FROM employees WHERE employee_id = 'EMP002' OR employee_id = 'EMP001'"),
    ("Different column", "SELECT name FROM employees WHERE email = 'x@example.com'"),
    ("Salary", "SELECT salary FROM employees"),
    ("Star", "SELECT * FROM employees"),
    ("Wrong table", "SELECT name FROM users"),
    ("Multiple statements", "SELECT name FROM employees; DELETE FROM employees"),
        ("JOIN unauthorized", """
        SELECT employees.name
        FROM employees
        JOIN users ON employees.employee_id = users.employee_id
    """),

    ("Subquery unauthorized", """
        SELECT name
        FROM employees
        WHERE employee_id IN (
            SELECT employee_id FROM users
        )
    """),

    ("Authorized self-filter", """
        SELECT name
        FROM employees
        WHERE employee_id = 'EMP002'
        AND email = 'x@example.com'
    """),
]

for name, sql in tests:
    print(f"\n{name}:")
    print(authorize_sql(sql, columns, tables, row))