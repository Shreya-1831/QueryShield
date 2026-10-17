from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import database_auth


client = TestClient(app)


def test_database_auth_rejects_employee_id_spoofing(monkeypatch):
    """
    A user authenticated as EMP002 must not be able
    to request database authentication as EMP001.
    """

    monkeypatch.setattr(
        database_auth.identity_service,
        "resolve",
        lambda: {
            "user_id": 2,
            "employee_id": "EMP002",
            "username": "employee2",
            "role": "Employee",
        },
    )

    response = client.get(
        "/api/auth/database/EMP001"
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Employee ID does not match authenticated identity"
    )