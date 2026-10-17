from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_admin_can_view_models():
    identity = {
        "username": "admin",
        "employee_id": "EMP001",
        "role": "Admin"
    }

    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=identity
    ):
        response = client.get("/api/admin/models")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "models" in data


def test_employee_cannot_view_models():
    identity = {
        "username": "employee",
        "employee_id": "EMP002",
        "role": "Employee"
    }

    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=identity
    ):
        response = client.get("/api/admin/models")

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_models():
    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=None
    ):
        response = client.get("/api/admin/models")

    assert response.status_code == 401


def test_admin_can_select_approved_model():
    identity = {
        "username": "admin",
        "employee_id": "EMP001",
        "role": "Admin"
    }

    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=identity
    ), patch(
        "app.api.routes.models.is_model_available",
        return_value=True
    ):
        response = client.post(
            "/api/admin/models/select",
            params={"model_id": 1}
        )

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["model"]["model_id"] == 1
    assert data["model"]["status"] == "ACTIVE"
    assert data["model"]["approved"] is True


def test_admin_cannot_select_model_not_installed():
    identity = {
        "username": "admin",
        "employee_id": "EMP001",
        "role": "Admin"
    }

    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=identity
    ), patch(
        "app.api.routes.models.is_model_available",
        return_value=False
    ):
        response = client.post(
            "/api/admin/models/select",
            params={"model_id": 1}
        )

    assert response.status_code == 409
    assert "not installed" in response.json()["detail"]


def test_admin_cannot_select_model_when_ollama_is_unavailable():
    import requests

    identity = {
        "username": "admin",
        "employee_id": "EMP001",
        "role": "Admin"
    }

    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=identity
    ), patch(
        "app.api.routes.models.is_model_available",
        side_effect=requests.ConnectionError("Ollama unavailable")
    ):
        response = client.post(
            "/api/admin/models/select",
            params={"model_id": 1}
        )

    assert response.status_code == 503
    assert "Ollama is unavailable" in response.json()["detail"]


def test_employee_cannot_select_model():
    identity = {
        "username": "employee",
        "employee_id": "EMP002",
        "role": "Employee"
    }

    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=identity
    ):
        response = client.post(
            "/api/admin/models/select",
            params={"model_id": 1}
        )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_select_model():
    with patch(
        "app.api.routes.models.identity_service.resolve",
        return_value=None
    ):
        response = client.post(
            "/api/admin/models/select",
            params={"model_id": 1}
        )

    assert response.status_code == 401