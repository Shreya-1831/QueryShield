import pytest
from sqlalchemy import text

from app.database.connection_manager import db_manager


def test_admin_connection():
    with db_manager.connect("Admin") as db:
        user = db.execute(text("SELECT CURRENT_USER()")).scalar()
        count = db.execute(text("SELECT COUNT(*) FROM employees")).scalar()

    assert "queryshield_admin" in user
    assert count == 26


def test_employee_connection():
    with db_manager.connect("Employee") as db:
        user = db.execute(text("SELECT CURRENT_USER()")).scalar()
        count = db.execute(text("SELECT COUNT(*) FROM employees")).scalar()

    assert "queryshield_employee" in user
    assert count == 26


def test_invalid_role_rejected():
    with pytest.raises(ValueError, match="Unsupported role"):
        db_manager.connect("Unknown")


def test_query_timeout_configured():
    with db_manager.connect("Admin") as db:
        value = db.execute(text("SELECT @@SESSION.MAX_EXECUTION_TIME")).scalar()
    assert value == 10000


@pytest.mark.parametrize("role", ["Admin", "Employee"])
def test_role_database_is_read_only(role):
    with db_manager.connect(role) as db:
        grants = db.execute(text("SHOW GRANTS FOR CURRENT_USER()")).scalars().all()

    dangerous = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT OPTION")
    assert not any(any(word in grant.upper() for word in dangerous) for grant in grants)