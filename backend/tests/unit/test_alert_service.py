
import uuid

import pytest
from sqlalchemy import bindparam, text

from app.database.connection import engine
from app.monitoring.alert_service import alert_service


@pytest.fixture(autouse=True)
def isolate_test_alerts(monkeypatch):
    created_ids = []
    test_prefix = f"TEST-{uuid.uuid4().hex}-"
    original_raise_alert = alert_service.raise_alert

    def tracked_raise_alert(
        alert_type,
        severity,
        details,
        *args,
        **kwargs,
    ):
        # Give every test unique details to avoid matching real alerts.
        test_details = f"{test_prefix}{details}"

        alert = original_raise_alert(
            alert_type,
            severity,
            test_details,
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

    # Delete only alerts created by this test.
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


def health(**kwargs):
    return {
        "database": {
            "status": "healthy",
            "latency_ms": 10,
            "connections": {
                "pool_size": 5,
                "checked_out": 1,
            },
        },
        "ollama": {
            "status": "healthy",
            "latency_ms": 10,
        },
        "gpu": {
            "status": "healthy",
            "utilization_percent": 10,
            "memory_percent": 10,
            "temperature_c": 50,
        },
        "system": {
            "cpu_percent": 10,
            "ram_percent": 10,
            "disk_percent": 10,
        },
        **kwargs,
    }


def test_raise_alert():
    alert = alert_service.raise_alert(
        "database_failure",
        "critical",
        "DB unavailable",
    )

    assert alert["type"] == "database_failure"
    assert alert["severity"] == "critical"
    assert not alert["resolved"]


def test_duplicate_alert():
    alert_service.raise_alert(
        "database_failure",
        "critical",
        "DB unavailable",
    )

    assert alert_service.raise_alert(
        "database_failure",
        "critical",
        "DB unavailable",
    ) is None


def test_list_active():
    alert = alert_service.raise_alert(
        "model_failure",
        "high",
        "Ollama unavailable",
    )

    active_alerts = alert_service.list_alerts(
        unresolved_only=True
    )

    assert any(
        item["id"] == alert["id"]
        for item in active_alerts
    )


def test_resolve():
    alert = alert_service.raise_alert(
        "cpu_exhaustion",
        "high",
        "CPU > 90%",
    )

    resolved = alert_service.resolve(alert["id"])

    assert resolved is not None
    assert resolved["resolved"]


def test_unknown():
    assert alert_service.resolve(-1) is None


def test_database_failure():
    alerts = alert_service.check_health(
        health(database={"status": "unhealthy"})
    )

    assert alerts[0]["type"] == "database_failure"


def test_model_failure():
    alerts = alert_service.check_health(
        health(ollama={"status": "unhealthy"})
    )

    assert alerts[0]["type"] == "model_failure"


def test_resource_exhaustion():
    alerts = alert_service.check_health(
        health(
            system={
                "cpu_percent": 95,
                "ram_percent": 10,
                "disk_percent": 10,
            }
        )
    )

    assert alerts[0]["type"] == "resource_exhaustion"


def test_gpu_exhaustion():
    alerts = alert_service.check_health(
        health(
            gpu={
                "status": "healthy",
                "utilization_percent": 97,
                "memory_percent": 10,
                "temperature_c": 50,
            }
        )
    )

    assert alerts[0]["type"] == "gpu_exhaustion"


def test_gpu_memory():
    alerts = alert_service.check_health(
        health(
            gpu={
                "status": "healthy",
                "utilization_percent": 10,
                "memory_percent": 97,
                "temperature_c": 50,
            }
        )
    )

    assert alerts[0]["type"] == "gpu_memory_exhaustion"


def test_gpu_temperature():
    alerts = alert_service.check_health(
        health(
            gpu={
                "status": "healthy",
                "utilization_percent": 10,
                "memory_percent": 10,
                "temperature_c": 90,
            }
        )
    )

    assert alerts[0]["type"] == "gpu_temperature"


def test_connection_exhaustion():
    alerts = alert_service.check_health(
        health(
            database={
                "status": "healthy",
                "latency_ms": 10,
                "connections": {
                    "pool_size": 5,
                    "checked_out": 5,
                },
            }
        )
    )

    assert alerts[0]["type"] == "connection_exhaustion"


def test_latency():
    alerts = alert_service.check_health(
        health(
            database={
                "status": "healthy",
                "latency_ms": 6000,
                "connections": {
                    "pool_size": 5,
                    "checked_out": 1,
                },
            }
        )
    )

    assert alerts[0]["type"] == "excessive_latency"


def test_security_alert():
    alert = alert_service.security_alert(
        "suspicious_activity",
        "Repeated unauthorized requests",
    )

    assert alert["severity"] == "high"