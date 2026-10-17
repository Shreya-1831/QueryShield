from app.privacy.privacy_service import (
    PrivacyContext,
    PrivacyService,
)


def employee_context():
    return PrivacyContext(
        employee_id="EMP002",
        role="Employee",
        allowed_columns={
            "employees": {
                "employee_id",
                "name",
                "salary",
                "phone",
                "address",
            }
        },
        privacy_rules={
            "employees": {
                "salary": {
                    "sensitivity": "sensitive",
                    "action": "allow",
                },
                "phone": {
                    "sensitivity": "sensitive",
                    "action": "allow",
                },
                "address": {
                    "sensitivity": "sensitive",
                    "action": "allow",
                },
            }
        },
    )


def test_allowed_result_passes_unchanged():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "name": "Employee 2",
            "salary": 60000,
        }
    ]

    opa_decision = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "name": "allow",
            "salary": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert result.rows == rows
    assert result.leakage_detected is False
    assert result.blocked is False
    assert result.masked_fields == 0
    assert result.removed_fields == 0


def test_opa_mask_action():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "salary": 75000,
        }
    ]

    opa_decision = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "salary": "mask",
        },
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert result.rows[0]["employee_id"] == "EMP002"
    assert result.rows[0]["salary"] != 75000
    assert result.masked_fields == 1
    assert result.blocked is False


def test_opa_remove_action():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "salary": 75000,
        }
    ]

    opa_decision = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "salary": "remove",
        },
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert "salary" not in result.rows[0]
    assert result.removed_fields == 1
    assert result.leakage_detected is True
    assert result.blocked is False


def test_opa_blocks_result():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "salary": 75000,
        }
    ]

    opa_decision = {
        "allowed": False,
        "reason": "Column access denied",
        "actions": {},
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert result.rows == []
    assert result.blocked is True
    assert result.leakage_detected is True
    assert "Column access denied" in result.reasons


def test_unauthorized_action_removes_field():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "name": "Employee 2",
            "internal_secret": "TOP_SECRET",
        }
    ]

    opa_decision = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "name": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert "internal_secret" not in result.rows[0]
    assert result.removed_fields == 1
    assert result.leakage_detected is True


def test_empty_result():
    service = PrivacyService()

    result = service.protect(
        [],
        employee_context(),
        "employees",
        {
            "allowed": True,
            "actions": {},
        },
    )

    assert result.rows == []
    assert result.leakage_detected is False
    assert result.blocked is False


def test_phone_allowed():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "phone": "9876543210",
        }
    ]

    opa_decision = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "phone": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert result.rows[0]["phone"] == "9876543210"
    assert result.leakage_detected is False


def test_address_allowed():
    service = PrivacyService()

    rows = [
        {
            "employee_id": "EMP002",
            "address": "Chennai",
        }
    ]

    opa_decision = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "address": "allow",
        },
    }

    result = service.protect(
        rows,
        employee_context(),
        "employees",
        opa_decision,
    )

    assert result.rows[0]["address"] == "Chennai"
    assert result.leakage_detected is False