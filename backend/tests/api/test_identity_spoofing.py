from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.query import identity_service


client = TestClient(app)


def test_employee_id_spoofing_is_rejected(monkeypatch):
    """
    Client must not be able to provide a different Employee ID.
    Identity must come from the server-side identity service.
    """

    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "user_id": 1,
            "employee_id": "EMP002",
            "username": "employee2",
            "role": "Employee",
        },
    )

    response = client.post(
        "/api/query",
        json={
            "prompt": "Show my name",
            "employee_id": "EMP001",
        },
    )

    assert response.status_code == 422


def test_role_spoofing_is_rejected(monkeypatch):
    """
    Client must not be able to supply Admin role.
    """

    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "user_id": 2,
            "employee_id": "EMP002",
            "username": "employee2",
            "role": "Employee",
        },
    )

    response = client.post(
        "/api/query",
        json={
            "prompt": "Show all employee salaries",
            "role": "Admin",
        },
    )

    assert response.status_code == 422


def test_employee_id_and_role_spoofing_together_is_rejected(monkeypatch):
    """
    Supplying both Employee ID and role must not alter
    the authenticated server-side identity.
    """

    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "user_id": 2,
            "employee_id": "EMP002",
            "username": "employee2",
            "role": "Employee",
        },
    )

    response = client.post(
        "/api/query",
        json={
            "prompt": "Show all employee salaries",
            "employee_id": "EMP001",
            "role": "Admin",
        },
    )

    assert response.status_code == 422