from app.security.sql_hardener import harden_sql


def test_select_allowed():
    ok, reason, sql = harden_sql("SELECT name FROM employees")
    assert ok
    assert "LIMIT 500" in sql


def test_non_select_blocked():
    ok, _, sql = harden_sql("DELETE FROM employees")
    assert not ok
    assert sql is None


def test_too_many_joins_blocked():
    sql = """
    SELECT e.name
    FROM employees e
    JOIN departments d ON e.department_id = d.id
    JOIN t1 ON t1.id = e.id
    JOIN t2 ON t2.id = e.id
    JOIN t3 ON t3.id = e.id
    """
    ok, reason, _ = harden_sql(sql)
    assert not ok
    assert reason == "Query is too complex"


def test_too_many_subqueries_blocked():
    sql = """
    SELECT name FROM employees
    WHERE id IN (
        SELECT id FROM employees
        WHERE id IN (
            SELECT id FROM employees
            WHERE id IN (
                SELECT id FROM employees
            )
        )
    )
    """
    ok, reason, _ = harden_sql(sql)
    assert not ok
    assert reason == "Too many subqueries"


def test_large_limit_reduced():
    ok, _, sql = harden_sql("SELECT name FROM employees LIMIT 1000")
    assert ok
    assert "LIMIT 500" in sql


def test_small_limit_preserved():
    ok, _, sql = harden_sql("SELECT name FROM employees LIMIT 100")
    assert ok
    assert "LIMIT 100" in sql


def test_zero_limit_preserved():
    ok, _, sql = harden_sql("SELECT name FROM employees LIMIT 0")
    assert ok
    assert "LIMIT 0" in sql