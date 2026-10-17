from app.audit.audit_service import AuditService


def test_resolve_employee_to_user():
    service = AuditService()

    user_id = service._get_user_id("EMP001")

    assert user_id == 1


def test_record_query():
    service = AuditService()

    query_id = service.record_query(
        employee_id="EMP001",
        prompt="Show my department",
        generated_sql="SELECT department FROM employees",
        status="SUCCESS",
        intent="DATA_RETRIEVAL",
        risk_level="LOW",
        authorized_sql="SELECT department FROM employees",
        authorization_decision="ALLOWED",
        privacy_decision="ALLOWED",
        execution_status="SUCCESS",
        row_count=1,
        execution_time_ms=10,
        total_time_ms=20,
    )

    assert query_id is not None


def test_record_security_event():
    service = AuditService()

    event_id = service.record_security_event(
        employee_id="EMP002",
        event_type="TEST_SECURITY_EVENT",
        description="Audit service test event",
    )

    assert event_id is not None

