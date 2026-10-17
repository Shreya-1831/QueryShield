
from datetime import datetime, timezone

from sqlalchemy import text

from app.database.connection import engine


class AlertService:
    def __init__(self, db_engine=None):
        self._engine = db_engine or engine

    @staticmethod
    def _serialize(row):
        created_at = row["created_at"]
        resolved_at = row["resolved_at"]

        return {
            "id": row["alert_id"],
            "type": row["alert_type"],
            "severity": row["severity"],
            "details": row["details"],
            "user_id": row["user_id"],
            "source_event_id": row["source_event_id"],
            "created_at": (
                created_at.isoformat() if created_at else None
            ),
            "resolved": resolved_at is not None,
            "resolved_at": (
                resolved_at.isoformat() if resolved_at else None
            ),
        }

    def raise_alert(
        self,
        alert_type,
        severity,
        details,
        user_id=None,
        source_event_id=None,
        connection=None,
    ):
        # Reuse an existing transaction when one is supplied.
        if connection is not None:
            return self._raise_alert(
                connection,
                alert_type,
                severity,
                details,
                user_id,
                source_event_id,
            )

        with self._engine.begin() as db:
            return self._raise_alert(
                db,
                alert_type,
                severity,
                details,
                user_id,
                source_event_id,
            )

    def _raise_alert(
        self,
        db,
        alert_type,
        severity,
        details,
        user_id,
        source_event_id,
    ):
        existing = db.execute(
            text("""
                SELECT alert_id
                FROM alerts
                WHERE alert_type = :alert_type
                  AND details = :details
                  AND resolved_at IS NULL
                LIMIT 1
                FOR UPDATE
            """),
            {
                "alert_type": alert_type,
                "details": details,
            },
        ).first()

        if existing:
            return None

        result = db.execute(
            text("""
                INSERT INTO alerts (
                    alert_type,
                    severity,
                    details,
                    user_id,
                    source_event_id
                )
                VALUES (
                    :alert_type,
                    :severity,
                    :details,
                    :user_id,
                    :source_event_id
                )
            """),
            {
                "alert_type": alert_type,
                "severity": severity.lower(),
                "details": details,
                "user_id": user_id,
                "source_event_id": source_event_id,
            },
        )

        row = db.execute(
            text("""
                SELECT alert_id, alert_type, severity, details,
                       user_id, source_event_id, created_at, resolved_at
                FROM alerts
                WHERE alert_id = :alert_id
            """),
            {"alert_id": result.lastrowid},
        ).mappings().one()

        return self._serialize(row)

    def check_health(self, health):
        alerts = []

        if health["database"]["status"] != "healthy":
            alerts.append(
                self.raise_alert(
                    "database_failure",
                    "critical",
                    "Database unavailable",
                )
            )

        if health["ollama"]["status"] != "healthy":
            alerts.append(
                self.raise_alert(
                    "model_failure",
                    "critical",
                    "Ollama unavailable",
                )
            )

        system = health["system"]

        for name in ("cpu_percent", "ram_percent", "disk_percent"):
            if system[name] >= 90:
                alerts.append(
                    self.raise_alert(
                        "resource_exhaustion",
                        "high",
                        f"{name} exceeded 90%",
                    )
                )

        gpu = health.get("gpu", {})

        if gpu.get("status") == "healthy":
            if gpu.get("utilization_percent", 0) >= 95:
                alerts.append(
                    self.raise_alert(
                        "gpu_exhaustion",
                        "high",
                        "GPU utilization exceeded 95%",
                    )
                )

            if gpu.get("memory_percent", 0) >= 95:
                alerts.append(
                    self.raise_alert(
                        "gpu_memory_exhaustion",
                        "high",
                        "GPU memory exceeded 95%",
                    )
                )

            if gpu.get("temperature_c", 0) >= 85:
                alerts.append(
                    self.raise_alert(
                        "gpu_temperature",
                        "high",
                        "GPU temperature exceeded 85C",
                    )
                )

        connections = health["database"].get("connections", {})
        pool_size = connections.get("pool_size", 0)
        checked_out = connections.get("checked_out", 0)

        if pool_size and checked_out >= pool_size:
            alerts.append(
                self.raise_alert(
                    "connection_exhaustion",
                    "high",
                    "Database connection pool exhausted",
                )
            )

        for service in ("database", "ollama"):
            latency = health[service].get("latency_ms")

            if latency is not None and latency >= 5000:
                alerts.append(
                    self.raise_alert(
                        "excessive_latency",
                        "high",
                        f"{service} latency exceeded 5000 ms",
                    )
                )

        return [alert for alert in alerts if alert is not None]

    def security_alert(
        self,
        event_type,
        details,
        user_id=None,
        source_event_id=None,
        connection=None,
    ):
        return self.raise_alert(
            event_type,
            "high",
            details,
            user_id=user_id,
            source_event_id=source_event_id,
            connection=connection,
        )

    def list_alerts(self, unresolved_only=False):
        query = """
            SELECT alert_id, alert_type, severity, details,
                   user_id, source_event_id, created_at, resolved_at
            FROM alerts
        """

        if unresolved_only:
            query += " WHERE resolved_at IS NULL"

        query += " ORDER BY created_at DESC, alert_id DESC"

        with self._engine.connect() as db:
            rows = db.execute(text(query)).mappings().all()
            return [self._serialize(row) for row in rows]

    def resolve(self, alert_id):
        with self._engine.begin() as db:
            existing = db.execute(
                text("""
                    SELECT alert_id
                    FROM alerts
                    WHERE alert_id = :alert_id
                    FOR UPDATE
                """),
                {"alert_id": alert_id},
            ).first()

            if existing is None:
                return None

            db.execute(
                text("""
                    UPDATE alerts
                    SET resolved_at = CURRENT_TIMESTAMP
                    WHERE alert_id = :alert_id
                      AND resolved_at IS NULL
                """),
                {"alert_id": alert_id},
            )

            row = db.execute(
                text("""
                    SELECT alert_id, alert_type, severity, details,
                           user_id, source_event_id,
                           created_at, resolved_at
                    FROM alerts
                    WHERE alert_id = :alert_id
                """),
                {"alert_id": alert_id},
            ).mappings().one()

            return self._serialize(row)

    def clear(self):
        raise RuntimeError(
            "Clearing persistent alerts is disabled. "
            "Use isolated test data and explicit test cleanup."
        )


alert_service = AlertService()
