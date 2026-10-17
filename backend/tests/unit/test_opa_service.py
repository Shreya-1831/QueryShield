from app.privacy.opa_service import OPAService


def test_opa_allows_valid_result():
    service = OPAService()

    input_data = {
        "result_columns": [
            "employee_id",
            "name",
            "salary",
            "date_of_birth",
        ],
        "allowed_columns": [
            "employee_id",
            "name",
            "salary",
            "date_of_birth",
        ],
        "privacy_rules": {
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
        },
    }

    result = service.evaluate(input_data)

    assert result["allowed"] is True
    assert result["actions"]["salary"] == "mask"
    assert result["actions"]["date_of_birth"] == "mask"


def test_opa_blocks_unauthorized_column():
    service = OPAService()

    input_data = {
        "result_columns": [
            "employee_id",
            "name",
            "phone",
        ],
        "allowed_columns": {
            "employee_id": True,
            "name": True,
        },
        "privacy_rules": {
            "employee_id": {
                "sensitivity": "normal",
                "action": "allow",
            },
            "name": {
                "sensitivity": "normal",
                "action": "allow",
            },
        },
    }

    result = service.evaluate(input_data)

    assert result["allowed"] is False
    assert result["reason"] == "policy_violation"