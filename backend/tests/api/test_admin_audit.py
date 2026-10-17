from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_can_view_audit_logs():
    with patch(
        "app.api.routes.audit.identity_service.resolve",
        return_value={
            "employee_id": "EMP001",
            "role": "Admin",
        },
    ), patch(
        "app.api.routes.audit.engine"
    ) as mock_engine:

        mock_db = (
            mock_engine.connect
            .return_value
            .__enter__
            .return_value
        )

        mock_db.execute.return_value.mappings.return_value.all.return_value = [
            {
                "query_id": 1,
                "employee_id": "EMP001",
                "username": "admin",
                "prompt": "Show employee count",
                "intent": "aggregation",
                "generated_sql": "SELECT COUNT(*) FROM employees",
                "authorized_sql": "SELECT COUNT(*) FROM employees",
                "risk_level": "LOW",
                "authorization_decision": "ALLOWED",
                "privacy_decision": "ALLOWED",
                "execution_status": "SUCCESS",
                "status": "SUCCESS",
                "row_count": 1,
                "execution_time_ms": 20,
                "total_time_ms": 35,
                "created_at": "2026-10-07T09:00:00",
            }
        ]

        response = client.get("/api/admin/audit")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["count"] == 1
    assert data["audit_logs"][0]["employee_id"] == "EMP001"


def test_employee_cannot_view_audit_logs():
    with patch(
        "app.api.routes.audit.identity_service.resolve",
        return_value={
            "employee_id": "EMP002",
            "role": "Employee",
        },
    ):
        response = client.get("/api/admin/audit")

    assert response.status_code == 403


def test_unauthenticated_cannot_view_audit_logs():
    with patch(
        "app.api.routes.audit.identity_service.resolve",
        return_value=None,
    ):
        response = client.get("/api/admin/audit")

    assert response.status_code == 401


def test_admin_can_filter_audit_logs():
    with patch(
        "app.api.routes.audit.identity_service.resolve",
        return_value={
            "employee_id": "EMP001",
            "role": "Admin",
        },
    ), patch(
        "app.api.routes.audit.engine"
    ) as mock_engine:

        mock_db = (
            mock_engine.connect
            .return_value
            .__enter__
            .return_value
        )

        mock_db.execute.return_value.mappings.return_value.all.return_value = []

        response = client.get(
            "/api/admin/audit"
            "?employee_id=EMP002"
            "&status=BLOCKED"
            "&risk_level=HIGH"
            "&limit=25"
        )

    assert response.status_code == 200
    assert response.json()["success"] is True

    executed_sql = str(
        mock_db.execute.call_args.args[0]
    )

    assert "employee_id" in executed_sql
    assert "status" in executed_sql
    assert "risk_level" in executed_sql