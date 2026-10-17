from app.security.sql_authorizer import authorize_sql


ALLOWED_TABLES = {"employees", "departments"}

ALLOWED_COLUMNS = {
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
    "department_name",
}

ROW_CONDITION = "employee_id = 'EMP002'"


TESTS = [
    (
        "VALID-01",
        "SELECT name FROM employees WHERE employee_id = 'EMP002'",
        True,
    ),
    (
        "VALID-02",
        "SELECT name, email FROM employees WHERE employee_id = 'EMP002'",
        True,
    ),
    (
        "IN-01",
        "SELECT salary FROM employees WHERE employee_id IN ('EMP001', 'EMP002')",
        False,
    ),
    (
        "IN-02",
        "SELECT salary FROM employees WHERE employee_id IN "
        "(SELECT employee_id FROM employees)",
        False,
    ),
    (
        "NOT-01",
        "SELECT salary FROM employees WHERE employee_id != 'EMP002'",
        False,
    ),
    (
        "OR-01",
        "SELECT salary FROM employees "
        "WHERE employee_id = 'EMP002' OR employee_id = 'EMP001'",
        False,
    ),
    (
        "NOT-02",
        "SELECT salary FROM employees "
        "WHERE NOT employee_id = 'EMP002'",
        False,
    ),
    (
        "UNION-01",
        "SELECT name FROM employees WHERE employee_id = 'EMP002' "
        "UNION SELECT salary FROM employees",
        False,
    ),
    (
        "STAR-01",
        "SELECT * FROM employees WHERE employee_id = 'EMP002'",
        False,
    ),
    (
        "TABLE-01",
        "SELECT name FROM users WHERE employee_id = 'EMP002'",
        False,
    ),
    (
        "COLUMN-01",
        "SELECT password FROM employees WHERE employee_id = 'EMP002'",
        False,
    ),
    (
        "DELETE-01",
        "DELETE FROM employees WHERE employee_id = 'EMP002'",
        False,
    ),
    (
        "UPDATE-01",
        "UPDATE employees SET salary = 1 WHERE employee_id = 'EMP002'",
        False,
    ),
    (
        "DROP-01",
        "DROP TABLE employees",
        False,
    ),
    (
        "MULTI-01",
        "SELECT name FROM employees WHERE employee_id = 'EMP002'; "
        "SELECT salary FROM employees",
        False,
    ),
    (
        "ALIAS-01",
        "SELECT e.name FROM employees e "
        "WHERE e.employee_id = 'EMP002'",
        True,
    ),
    (
        "ALIAS-02",
        "SELECT e.salary FROM employees e "
        "WHERE e.employee_id = 'EMP001'",
        False,
    ),
    (
        "JOIN-01",
        "SELECT e.name, d.department_name "
        "FROM employees e "
        "JOIN departments d ON e.department_id = d.department_id "
        "WHERE e.employee_id = 'EMP002'",
        True,
    ),
    (
        "JOIN-02",
        "SELECT e.name, e.salary "
        "FROM employees e "
        "JOIN departments d ON e.department_id = d.department_id "
        "WHERE e.employee_id = 'EMP001'",
        False,
    ),
    # (
    #     "BROAD-01",
    #     "SELECT name FROM employees",
    #     False,
    # ),
]


def run_tests():
    passed = 0
    failed = 0

    print("\n" + "=" * 80)
    print("QUERYSHIELD SQL SECURITY TEST")
    print("=" * 80)

    for test_id, sql, expected in TESTS:

        print("\n" + "-" * 80)
        print(f"[{test_id}]")
        print(f"SQL: {sql}")
        print(f"EXPECTED: {expected}")

        try:
            authorized, reason, authorized_sql = authorize_sql(
                sql,
                ALLOWED_COLUMNS,
                ALLOWED_TABLES,
                ROW_CONDITION,
            )

            print(f"AUTHORIZED: {authorized}")
            print(f"REASON: {reason}")

            if authorized_sql:
                print(f"SQL: {authorized_sql}")

            if authorized == expected:
                passed += 1
                print("STATUS: PASS")
            else:
                failed += 1
                print("STATUS: FAIL")

        except Exception as e:
            failed += 1
            print(f"ERROR: {type(e).__name__}: {e}")
            print("STATUS: FAIL")

    print("\n" + "=" * 80)
    print("FINAL SQL SECURITY RESULT")
    print("=" * 80)
    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Total  : {len(TESTS)}")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()