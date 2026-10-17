import os
import subprocess
import time
import psutil
import requests
from sqlalchemy import text
from app.database.connection import engine


class HealthService:
    def database(self):
        start = time.perf_counter()
        try:
            with engine.connect() as db:
                db.execute(text("SELECT 1"))

            pool = engine.pool
            return {
                "status": "healthy",
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "connections": {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                },
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def ollama(self):
        start = time.perf_counter()
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            return {
                "status": "healthy" if r.ok else "unhealthy",
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def gpu(self):
        try:
            r = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if r.returncode != 0:
                return {"status": "unavailable"}

            utilization, used, total, temperature = map(
                float, r.stdout.strip().split(",")
            )

            return {
                "status": "healthy",
                "utilization_percent": utilization,
                "memory_used_mb": used,
                "memory_total_mb": total,
                "memory_percent": round((used / total) * 100, 2) if total else 0,
                "temperature_c": temperature,
            }
        except Exception:
            return {"status": "unavailable"}

    def system(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(os.path.abspath(os.sep)).percent,
        }

    def all(self):
        db = self.database()
        ollama = self.ollama()
        gpu = self.gpu()
        system = self.system()

        healthy = (
            db["status"] == "healthy"
            and ollama["status"] == "healthy"
        )

        return {
            "status": "healthy" if healthy else "unhealthy",
            "fastapi": {"status": "healthy"},
            "database": db,
            "ollama": ollama,
            "gpu": gpu,
            "system": system,
        }


health_service = HealthService()