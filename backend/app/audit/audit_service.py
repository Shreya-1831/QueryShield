from typing import Optional

from sqlalchemy import text

from app.database.connection import engine
from app.monitoring.alert_service import alert_service


class AuditService:
    """
    Handles QueryShield audit logging.

    query_history:
        Stores query lifecycle and outcome.

    security_events:
        Stores security violations and generated alerts.
    """

    MONITORED_SECURITY_EVENTS = {
        "PROMPT_SECURITY_BLOCK",
        "POLICY_NOT_FOUND",
        "ROLE_MISMATCH",
        "BROAD_DATA_REQUEST",
        "SQL_AUTHORIZATION_FAILURE",
        "SQL_HARDENING_FAILURE",
    }

    SEVERITY_MAP = {
        "PROMPT_SECURITY_BLOCK": "HIGH",
        "POLICY_NOT_FOUND": "HIGH",
        "ROLE_MISMATCH": "CRITICAL",
        "BROAD_DATA_REQUEST": "HIGH",
        "SQL_AUTHORIZATION_FAILURE": "HIGH",
        "SQL_HARDENING_FAILURE": "CRITICAL",
        "SECURITY_ALERT": "CRITICAL",
    }

    REPEATED_EVENT_THRESHOLD = 3
    REPEATED_EVENT_WINDOW_MINUTES = 5

    def _get_user_id(self, employee_id: str) -> Optional[int]:
        with engine.connect() as db:
            return db.execute(
                text("""
                    SELECT user_id
                    FROM users
                    WHERE employee_id = :employee_id
                      AND is_active = 1
                    LIMIT 1
                """),
                {"employee_id": employee_id},
            ).scalar()

    def record_query(
        self,
        employee_id: str,
        prompt: str,
        generated_sql: Optional[str] = None,
        status: Optional[str] = None,
        intent: Optional[str] = None,
        risk_level: Optional[str] = None,
        authorized_sql: Optional[str] = None,
        authorization_decision: Optional[str] = None,
        privacy_decision: Optional[str] = None,
        execution_status: Optional[str] = None,
        row_count: Optional[int] = None,
        execution_time_ms: Optional[int] = None,
        total_time_ms: Optional[int] = None,
    ) -> Optional[int]:

        user_id = self._get_user_id(employee_id)

        if user_id is None:
            return None

        with engine.begin() as db:
            result = db.execute(
                text("""
                    INSERT INTO query_history (
                        user_id,
                        prompt,
                        generated_sql,
                        status,
                        intent,
                        risk_level,
                        authorized_sql,
                        authorization_decision,
                        privacy_decision,
                        execution_status,
                        row_count,
                        execution_time_ms,
                        total_time_ms
                    )
                    VALUES (
                        :user_id,
                        :prompt,
                        :generated_sql,
                        :status,
                        :intent,
                        :risk_level,
                        :authorized_sql,
                        :authorization_decision,
                        :privacy_decision,
                        :execution_status,
                        :row_count,
                        :execution_time_ms,
                        :total_time_ms
                    )
                """),
                {
                    "user_id": user_id,
                    "prompt": prompt,
                    "generated_sql": generated_sql,
                    "status": status,
                    "intent": intent,
                    "risk_level": risk_level,
                    "authorized_sql": authorized_sql,
                    "authorization_decision": authorization_decision,
                    "privacy_decision": privacy_decision,
                    "execution_status": execution_status,
                    "row_count": row_count,
                    "execution_time_ms": execution_time_ms,
                    "total_time_ms": total_time_ms,
                },
            )

            return result.lastrowid

    def _check_repeated_security_activity(
        self,
        db,
        user_id: int,
        event_type: str,
    ) -> bool:

        if event_type not in self.MONITORED_SECURITY_EVENTS:
            return False

        count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM security_events
                WHERE user_id = :user_id
                  AND event_type IN (
                      'PROMPT_SECURITY_BLOCK',
                      'POLICY_NOT_FOUND',
                      'ROLE_MISMATCH',
                      'BROAD_DATA_REQUEST',
                      'SQL_AUTHORIZATION_FAILURE',
                      'SQL_HARDENING_FAILURE'
                  )
                  AND created_at >= DATE_SUB(
                      NOW(),
                      INTERVAL :window_minutes MINUTE
                  )
            """),
            {
                "user_id": user_id,
                "window_minutes": self.REPEATED_EVENT_WINDOW_MINUTES,
            },
        ).scalar() or 0

        return count >= self.REPEATED_EVENT_THRESHOLD

    def _alert_already_created(self, db, user_id: int) -> bool:
        return db.execute(
            text("""
                SELECT 1
                FROM security_events
                WHERE user_id = :user_id
                  AND event_type = 'SECURITY_ALERT'
                  AND created_at >= DATE_SUB(
                      NOW(),
                      INTERVAL :window_minutes MINUTE
                  )
                LIMIT 1
            """),
            {
                "user_id": user_id,
                "window_minutes": self.REPEATED_EVENT_WINDOW_MINUTES,
            },
        ).first() is not None


    
    def get_query_history(
        self,
        employee_id: str,
        role: str,
        limit: int = 100,
    ) -> list[dict]:
        """Return query history belonging to the authenticated user."""

        user_id = self._get_user_id(employee_id)

        if user_id is None:
            return []

        # Limit the number of returned records.
        limit = max(1, min(limit, 500))

        with engine.connect() as db:
            rows = db.execute(
                text("""
                    SELECT
                        query_id,
                        prompt,
                        generated_sql,
                        status,
                        created_at,
                        intent,
                        risk_level,
                        authorization_decision,
                        privacy_decision,
                        execution_status,
                        row_count,
                        execution_time_ms,
                        total_time_ms
                    FROM query_history
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC, query_id DESC
                    LIMIT :limit
                """),
                {
                    "user_id": user_id,
                    "limit": limit,
                },
            ).mappings().all()

        return [
            {
                "query_id": row["query_id"],
                "prompt": row["prompt"],
                "generated_sql": row["generated_sql"],
                "status": row["status"],
                "created_at": (
                    row["created_at"].isoformat()
                    if row["created_at"] is not None
                    else None
                ),
                "intent": row["intent"],
                "risk_level": row["risk_level"],
                "authorization_decision": row["authorization_decision"],
                "privacy_decision": row["privacy_decision"],
                "execution_status": row["execution_status"],
                "row_count": row["row_count"],
                "execution_time_ms": row["execution_time_ms"],
                "total_time_ms": row["total_time_ms"],
            }
            for row in rows
        ]

    
    def record_security_event(
        self,
        employee_id: Optional[str],
        event_type: str,
        description: str,
        severity: Optional[str] = None,
    ) -> Optional[int]:

        user_id = (
            self._get_user_id(employee_id)
            if employee_id
            else None
        )

        resolved_severity = (
            severity
            or self.SEVERITY_MAP.get(event_type, "MEDIUM")
        ).upper()

        with engine.begin() as db:

            # 1. Persist the original security event.
            result = db.execute(
                text("""
                    INSERT INTO security_events (
                        user_id,
                        event_type,
                        severity,
                        details
                    )
                    VALUES (
                        :user_id,
                        :event_type,
                        :severity,
                        :details
                    )
                """),
                {
                    "user_id": user_id,
                    "event_type": event_type,
                    "severity": resolved_severity,
                    "details": description,
                },
            )

            event_id = result.lastrowid

            # 2. Detect repeated suspicious activity.
            if user_id is not None:
                repeated = self._check_repeated_security_activity(
                    db,
                    user_id,
                    event_type,
                )

                # 3. Generate one alert per user per time window.
                if repeated and not self._alert_already_created(
                    db,
                    user_id,
                ):
                    alert_details = (
                        "Repeated suspicious activity detected: "
                        "3 or more security violations occurred "
                        "within 5 minutes."
                    )

                    alert_event_result = db.execute(
                        text("""
                            INSERT INTO security_events (
                                user_id,
                                event_type,
                                severity,
                                details
                            )
                            VALUES (
                                :user_id,
                                'SECURITY_ALERT',
                                'CRITICAL',
                                :details
                            )
                        """),
                        {
                            "user_id": user_id,
                            "details": alert_details,
                        },
                    )

                    alert_event_id = alert_event_result.lastrowid

                    # 4. Insert the alert using the SAME transaction.
                    alert_service.raise_alert(
                        "SECURITY_ALERT",
                        "critical",
                        alert_details,
                        user_id=user_id,
                        source_event_id=alert_event_id,
                        connection=db,
                    )

            return event_id

audit_service = AuditService()