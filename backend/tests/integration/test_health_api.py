from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert all(k in r.json() for k in ("status", "fastapi", "database", "ollama", "gpu", "system"))


def test_database_health():
    r = client.get("/health/database")
    assert r.status_code == 200
    assert "status" in r.json()


def test_ollama_health():
    r = client.get("/health/ollama")
    assert r.status_code == 200
    assert "status" in r.json()


def test_system_health():
    r = client.get("/health/system")
    assert r.status_code == 200
    assert all(k in r.json() for k in ("cpu_percent", "ram_percent", "disk_percent"))


def test_gpu_health():
    r = client.get("/health/gpu")
    assert r.status_code == 200
    assert r.json()["status"] in ("healthy", "unavailable")