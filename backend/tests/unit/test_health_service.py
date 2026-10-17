from app.monitoring.health_service import health_service


def test_database_healthy(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "database",
        lambda: {
            "status": "healthy",
            "latency_ms": 1.0,
            "connections": {
                "pool_size": 5,
                "checked_in": 4,
                "checked_out": 1,
                "overflow": 0,
            },
        },
    )

    result = health_service.database()
    assert result["status"] == "healthy"


def test_ollama_healthy(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "ollama",
        lambda: {"status": "healthy", "latency_ms": 2.0},
    )

    assert health_service.ollama()["status"] == "healthy"


def test_gpu_healthy(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "gpu",
        lambda: {
            "status": "healthy",
            "utilization_percent": 45,
            "memory_used_mb": 4000,
            "memory_total_mb": 8000,
            "memory_percent": 50,
            "temperature_c": 60,
        },
    )

    result = health_service.gpu()

    assert result["status"] == "healthy"
    assert 0 <= result["utilization_percent"] <= 100
    assert 0 <= result["memory_percent"] <= 100
    assert result["temperature_c"] >= 0


def test_system_metrics():
    result = health_service.system()

    assert 0 <= result["cpu_percent"] <= 100
    assert 0 <= result["ram_percent"] <= 100
    assert 0 <= result["disk_percent"] <= 100


def test_all_healthy(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "database",
        lambda: {
            "status": "healthy",
            "latency_ms": 1.0,
            "connections": {
                "pool_size": 5,
                "checked_in": 4,
                "checked_out": 1,
                "overflow": 0,
            },
        },
    )

    monkeypatch.setattr(
        health_service,
        "ollama",
        lambda: {"status": "healthy", "latency_ms": 2.0},
    )

    monkeypatch.setattr(
        health_service,
        "gpu",
        lambda: {
            "status": "healthy",
            "utilization_percent": 40,
            "memory_used_mb": 3000,
            "memory_total_mb": 8000,
            "memory_percent": 37.5,
            "temperature_c": 55,
        },
    )

    monkeypatch.setattr(
        health_service,
        "system",
        lambda: {
            "cpu_percent": 10,
            "ram_percent": 20,
            "disk_percent": 30,
        },
    )

    result = health_service.all()

    assert result["status"] == "healthy"
    assert result["fastapi"]["status"] == "healthy"
    assert result["database"]["status"] == "healthy"
    assert result["ollama"]["status"] == "healthy"
    assert result["gpu"]["status"] == "healthy"
    assert result["system"]["cpu_percent"] == 10


def test_all_unhealthy_database(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "database",
        lambda: {
            "status": "unhealthy",
            "error": "DB unavailable",
        },
    )

    monkeypatch.setattr(
        health_service,
        "ollama",
        lambda: {"status": "healthy", "latency_ms": 2.0},
    )

    monkeypatch.setattr(
        health_service,
        "gpu",
        lambda: {"status": "healthy"},
    )

    monkeypatch.setattr(
        health_service,
        "system",
        lambda: {
            "cpu_percent": 10,
            "ram_percent": 20,
            "disk_percent": 30,
        },
    )

    assert health_service.all()["status"] == "unhealthy"


def test_all_unhealthy_ollama(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "database",
        lambda: {
            "status": "healthy",
            "latency_ms": 1.0,
            "connections": {
                "pool_size": 5,
                "checked_in": 4,
                "checked_out": 1,
                "overflow": 0,
            },
        },
    )

    monkeypatch.setattr(
        health_service,
        "ollama",
        lambda: {
            "status": "unhealthy",
            "error": "Ollama unavailable",
        },
    )

    monkeypatch.setattr(
        health_service,
        "gpu",
        lambda: {"status": "healthy"},
    )

    monkeypatch.setattr(
        health_service,
        "system",
        lambda: {
            "cpu_percent": 10,
            "ram_percent": 20,
            "disk_percent": 30,
        },
    )

    assert health_service.all()["status"] == "unhealthy"


def test_gpu_unavailable(monkeypatch):
    monkeypatch.setattr(
        health_service,
        "gpu",
        lambda: {"status": "unavailable"},
    )

    assert health_service.gpu()["status"] == "unavailable"