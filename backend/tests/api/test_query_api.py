from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
from unittest.mock import patch

def test_query_validation():
    response = client.post(
        "/api/query",
        json={"employee_id": "", "prompt": ""},
    )

    assert response.status_code == 422


def test_query_missing_fields():
    response = client.post(
        "/api/query",
        json={},
    )

    assert response.status_code == 422

def test_employee_id_spoofing_rejected():

    response = client.post(
        "/api/query",
        json={
            "employee_id": "EMP001",
            "prompt": "What is my salary?"
        },
    )

    assert response.status_code == 422


def test_role_spoofing_rejected():

    response = client.post(
        "/api/query",
        json={
            "role": "Admin",
            "prompt": "Show all employee salaries"
        },
    )

    assert response.status_code == 422


def test_user_id_spoofing_rejected():

    response = client.post(
        "/api/query",
        json={
            "user_id": "ADMIN001",
            "prompt": "Show all employee salaries"
        },
    )

    assert response.status_code == 422


def test_combined_identity_spoofing_rejected():

    response = client.post(
        "/api/query",
        json={
            "user_id": "ADMIN001",
            "employee_id": "EMP001",
            "role": "Admin",
            "prompt": "Show all employee salaries"
        },
    )

    assert response.status_code == 422

def test_query_uses_verified_identity():

    fake_identity = {
        "user_id": 2,
        "employee_id": "EMP002",
        "username": "employee2",
        "role": "Employee",
    }

    with patch(
        "app.api.routes.query.identity_service.resolve",
        return_value=fake_identity,
    ), patch(
        "app.api.routes.query.execute_query",
        return_value={
            "success": True,
            "data": []
        },
    ) as mock_execute:

        response = client.post(
            "/api/query",
            json={
                "prompt": "What is my name?"
            },
        )

    assert response.status_code == 200

    mock_execute.assert_called_once_with(
        "EMP002",
        "What is my name?",
        "Employee",
    )

def test_unauthorized_query_never_reaches_database():

    fake_identity = {
        "user_id": 2,
        "employee_id": "EMP002",
        "username": "employee2",
        "role": "Employee",
    }

    with patch(
        "app.api.routes.query.identity_service.resolve",
        return_value=fake_identity,
    ), patch(
        "app.api.routes.query.execute_query",
        return_value={
            "success": False,
            "stage": "authorization",
            "reason": "Access denied",
        },
    ) as mock_execute:

        response = client.post(
            "/api/query",
            json={
                "prompt": "Show me EMP001's salary"
            },
        )

    assert response.status_code == 200

    mock_execute.assert_called_once_with(
        "EMP002",
        "Show me EMP001's salary",
        "Employee",
    )