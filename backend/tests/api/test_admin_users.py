from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_can_view_users():
    with patch(
        "app.api.routes.users.identity_service.resolve",
        return_value={
            "employee_id": "EMP001",
            "role": "Admin",
        },
    ), patch(
        "app.api.routes.users.engine"
    ) as mock_engine:

        mock_db = mock_engine.connect.return_value.__enter__.return_value

        mock_db.execute.return_value.mappings.return_value.all.return_value = [
            {
                "employee_id": "EMP001",
                "username": "admin",
                "role_name": "Admin",
                "is_active": 1,
            }
        ]

        response = client.get("/api/admin/users")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["count"] == 1


def test_employee_cannot_view_users():
    with patch(
        "app.api.routes.users.identity_service.resolve",
        return_value={
            "employee_id": "EMP002",
            "role": "Employee",
        },
    ):
        response = client.get("/api/admin/users")

    assert response.status_code == 403


def test_unauthenticated_cannot_view_users():
    with patch(
        "app.api.routes.users.identity_service.resolve",
        return_value=None,
    ):
        response = client.get("/api/admin/users")

    assert response.status_code == 401