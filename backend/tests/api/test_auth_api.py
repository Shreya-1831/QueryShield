from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_me():
    response = client.get("/api/auth/me")
    assert response.status_code in (200, 401)