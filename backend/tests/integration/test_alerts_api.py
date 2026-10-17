
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import bindparam, text

from app.main import app
from app.api.routes.alerts import identity_service
from app.database.connection import engine
from app.monitoring.alert_service import alert_service

client = TestClient(app)


@pytest.fixture
def test_alert_cleanup(monkeypatch):
    created_ids = []
    prefix = f"TEST-{uuid.uuid4().hex}-"
    original_raise_alert = alert_service.raise_alert

    def tracked_raise_alert(
        alert_type,
        severity,
        details,
        *args,
        **kwargs,
    ):
        alert = original_raise_alert(
            alert_type,
            severity,
            f"{prefix}{details}",
            *args,
            **kwargs,
        )
        if alert is not None:
            created_ids.append(alert["id"])
        return alert

    monkeypatch.setattr(
        alert_service,
        "raise_alert",
        tracked_raise_alert,
    )

    yield

    if created_ids:
        with engine.begin() as db:
            db.execute(
                text("""
                    DELETE FROM alerts
                    WHERE alert_id IN :alert_ids
                """).bindparams(
                    bindparam("alert_ids", expanding=True)
                ),
                {"alert_ids": created_ids},
            )


@pytest.fixture
def admin_identity(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {"role": "Admin", "employee_id": "ADMIN001"},
    )


def test_alerts(admin_identity):
    response = client.get("/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_active_alerts(admin_identity, test_alert_cleanup):
    alert = alert_service.raise_alert(
        "database_failure", "critical", "DB unavailable"
    )

    response = client.get("/alerts/active")

    assert response.status_code == 200
    assert any(item["id"] == alert["id"] for item in response.json())


def test_resolve_alert(admin_identity, test_alert_cleanup):
    alert = alert_service.raise_alert(
        "model_failure", "critical", "Ollama unavailable"
    )

    response = client.post(f"/alerts/{alert['id']}/resolve")

    assert response.status_code == 200
    assert response.json()["resolved"] is True


def test_unknown_alert(admin_identity):
    response = client.post("/alerts/-1/resolve")
    assert response.status_code == 404


def test_employee_cannot_access_alerts(monkeypatch):
    monkeypatch.setattr(
        identity_service,
        "resolve",
        lambda: {"role": "Employee", "employee_id": "EMP001"},
    )

    assert client.get("/alerts").status_code == 403
    assert client.get("/alerts/active").status_code == 403
    assert client.post("/alerts/1/resolve").status_code == 403


def test_unverified_identity_cannot_access_alerts(monkeypatch):
    monkeypatch.setattr(
        identity_service, "resolve", lambda: None
    )

    assert client.get("/alerts").status_code == 401
    assert client.get("/alerts/active").status_code == 401
    assert client.post("/alerts/1/resolve").status_code == 401