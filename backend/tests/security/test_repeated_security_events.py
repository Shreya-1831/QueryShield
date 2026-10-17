from unittest.mock import MagicMock

from app.audit.audit_service import AuditService


class FakeResult:
    def __init__(self, scalar_value=None, lastrowid=1, first_value=None):
        self._scalar_value = scalar_value
        self.lastrowid = lastrowid
        self._first_value = first_value

    def scalar(self):
        return self._scalar_value

    def first(self):
        if self._first_value:
            return self._first_value
        return None


def test_repeated_security_activity_reaches_threshold():
    service = AuditService()

    db = MagicMock()

    # Current event has already been inserted.
    # COUNT(*) = 3, so threshold is reached.
    db.execute.side_effect = [
        FakeResult(scalar_value=3),
    ]

    result = service._check_repeated_security_activity(
        db,
        user_id=2,
        event_type="BROAD_DATA_REQUEST",
    )

    assert result is True


def test_single_security_event_does_not_reach_threshold():
    service = AuditService()

    db = MagicMock()

    db.execute.side_effect = [
        FakeResult(scalar_value=1),
    ]

    result = service._check_repeated_security_activity(
        db,
        user_id=2,
        event_type="BROAD_DATA_REQUEST",
    )

    assert result is False


def test_authorized_event_type_does_not_trigger_monitoring():
    service = AuditService()

    db = MagicMock()

    result = service._check_repeated_security_activity(
        db,
        user_id=2,
        event_type="AUTHORIZED_QUERY",
    )

    assert result is False
    db.execute.assert_not_called()


def test_alert_detection_prevents_duplicate_alert():
    service = AuditService()

    db = MagicMock()

    db.execute.return_value = FakeResult(
        first_value=(1,)
    )

    result = service._alert_already_created(
        db,
        user_id=2,
    )

    assert result is True

from unittest.mock import MagicMock, patch

from app.audit.audit_service import AuditService

def test_record_security_event_creates_alert_after_threshold():
    service = AuditService()
    fake_db = MagicMock()

    fake_insert_result = MagicMock()
    fake_insert_result.lastrowid = 123
    fake_db.execute.return_value = fake_insert_result

    with patch(
        "app.audit.audit_service.engine"
    ) as mock_engine, patch.object(
        service,
        "_get_user_id",
        return_value=1,
    ), patch.object(
        service,
        "_check_repeated_security_activity",
        return_value=True,
    ), patch.object(
        service,
        "_alert_already_created",
        return_value=False,
    ), patch(
        "app.audit.audit_service.alert_service"
    ) as mock_alert_service:

        mock_engine.begin.return_value.__enter__.return_value = fake_db

        result = service.record_security_event(
            employee_id="EMP001",
            event_type="SQL_AUTHORIZATION_FAILURE",
            description="Unauthorized SQL request blocked",
        )

    assert result == 123
    assert fake_db.execute.call_count == 2

    alert_sql = str(fake_db.execute.call_args_list[1].args[0])
    assert "SECURITY_ALERT" in alert_sql

    mock_alert_service.raise_alert.assert_called_once()

    args = mock_alert_service.raise_alert.call_args.args

    assert args[0] == "SECURITY_ALERT"
    assert args[1] == "critical"
    assert "Repeated suspicious activity detected" in args[2]

def test_repeated_security_event_does_not_create_duplicate_alert():
    service = AuditService()
    fake_db = MagicMock()

    fake_insert_result = MagicMock()
    fake_insert_result.lastrowid = 124
    fake_db.execute.return_value = fake_insert_result

    with patch(
        "app.audit.audit_service.engine"
    ) as mock_engine, patch.object(
        service,
        "_get_user_id",
        return_value=1,
    ), patch.object(
        service,
        "_check_repeated_security_activity",
        return_value=True,
    ), patch.object(
        service,
        "_alert_already_created",
        return_value=True,
    ), patch(
        "app.audit.audit_service.alert_service"
    ) as mock_alert_service:

        mock_engine.begin.return_value.__enter__.return_value = fake_db

        result = service.record_security_event(
            employee_id="EMP001",
            event_type="SQL_AUTHORIZATION_FAILURE",
            description="Unauthorized SQL request blocked",
        )

    assert result == 124

    # Only the original security event should be inserted.
    assert fake_db.execute.call_count == 1

    # No duplicate persistent alert.
    mock_alert_service.raise_alert.assert_not_called()

