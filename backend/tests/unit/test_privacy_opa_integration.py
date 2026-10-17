from app.privacy.opa_service import OPAService
from app.privacy.privacy_service import (
    PrivacyContext,
    PrivacyService,
)


def test_privacy_service_applies_opa_masking():

    opa = OPAService()
    privacy = PrivacyService()

    context = PrivacyContext(
        employee_id="EMP002",
        role="Employee",

        allowed_columns={
            "employees": {
                "employee_id",
                "name",
                "salary",
                "date_of_birth",
            }
        },

        privacy_rules={
            "employees": {
                "employee_id": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
                "name": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
                "salary": {
                    "sensitivity": "sensitive",
                    "action": "mask",
                },
                "date_of_birth": {
                    "sensitivity": "sensitive",
                    "action": "mask",
                },
            }
        },
    )

    rows = [
        {
            "employee_id": "EMP002",
            "name": "Priya Sharma",
            "salary": 55000,
            "date_of_birth": "2002-08-21",
        }
    ]

    opa_input = {
        "result_columns": list(rows[0].keys()),

        "allowed_columns": sorted(
            context.allowed_columns["employees"]
        ),

        "privacy_rules": context.privacy_rules["employees"],
    }

    decision = opa.evaluate(opa_input)

    result = privacy.protect(
        rows,
        context,
        "employees",
        decision,
    )

    assert result.blocked is False

    assert result.rows[0]["employee_id"] == "EMP002"
    assert result.rows[0]["name"] == "Priya Sharma"

    assert result.rows[0]["salary"] != 55000
    assert result.rows[0]["date_of_birth"] != "2002-08-21"

    assert result.masked_fields == 2


def test_privacy_service_blocks_opa_violation():

    opa = OPAService()
    privacy = PrivacyService()

    context = PrivacyContext(
        employee_id="EMP002",
        role="Employee",

        allowed_columns={
            "employees": {
                "employee_id",
                "name",
            }
        },

        privacy_rules={
            "employees": {
                "employee_id": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
                "name": {
                    "sensitivity": "normal",
                    "action": "allow",
                },
            }
        },
    )

    rows = [
        {
            "employee_id": "EMP002",
            "name": "Priya Sharma",
            "salary": 55000,
        }
    ]

    opa_input = {
        "result_columns": list(rows[0].keys()),

        "allowed_columns": {
            column: True
            for column in context.allowed_columns["employees"]
        },

        "privacy_rules": context.privacy_rules["employees"],
    }

    decision = opa.evaluate(opa_input)

    assert decision["allowed"] is False

    result = privacy.protect(
        rows,
        context,
        "employees",
        decision,
    )

    assert result.blocked is True
    assert result.rows == []