from fastapi.testclient import TestClient

from app.main import app
from app.identity.identity_service import identity_service


client = TestClient(app)


def test_admin_can_view_security_events(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "employee_id": "EMP001",
            "role": "Admin",
        },
    )

    response = client.get("/api/admin/security-events")

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert "events" in body
    assert isinstance(body["events"], list)


def test_employee_cannot_view_security_events(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "employee_id": "EMP002",
            "role": "Employee",
        },
    )

    response = client.get("/api/admin/security-events")

    assert response.status_code == 403


def test_unauthenticated_cannot_view_security_events(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: None,
    )

    response = client.get("/api/admin/security-events")

    assert response.status_code == 401

def test_admin_can_resolve_security_event(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "employee_id": "EMP001",
            "role": "Admin",
        },
    )

    response = client.post(
        "/api/admin/security-events/502/resolve"
    )

    assert response.status_code in (200, 404, 409)


def test_employee_cannot_resolve_security_event(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {
            "employee_id": "EMP002",
            "role": "Employee",
        },
    )

    response = client.post(
        "/api/admin/security-events/502/resolve"
    )

    assert response.status_code == 403


def test_unauthenticated_cannot_resolve_security_event(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: None,
    )

    response = client.post(
        "/api/admin/security-events/502/resolve"
    )

    assert response.status_code == 401