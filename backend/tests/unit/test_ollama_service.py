from unittest.mock import patch

import pytest

from app.ai.ollama_service import get_active_model



def test_get_active_model_returns_approved_active_model():
    fake_row = {
        "model_id": 1,
        "model_name": "qwen2.5-coder",
        "version": "7b",
        "approved": 1,
    }

    with patch(
        "app.ai.ollama_service.engine.connect"
    ) as mock_connect:
        mock_connection = (
            mock_connect.return_value.__enter__.return_value
        )

        mock_connection.execute.return_value \
            .mappings.return_value.all.return_value = [fake_row]

        model = get_active_model()

    assert model == "qwen2.5-coder:7b"


def test_get_active_model_fails_when_no_active_model():
    with patch(
        "app.ai.ollama_service.engine.connect"
    ) as mock_connect:
        mock_connection = (
            mock_connect.return_value.__enter__.return_value
        )

        mock_connection.execute.return_value \
            .mappings.return_value.all.return_value = []

        with pytest.raises(
            RuntimeError,
            match="No active model"
        ):
            get_active_model()


def test_get_active_model_fails_when_multiple_models_are_active():
    rows = [
        {
            "model_id": 1,
            "model_name": "qwen2.5-coder",
            "version": "7b",
            "approved": 1,
        },
        {
            "model_id": 2,
            "model_name": "llama3.2",
            "version": "3b",
            "approved": 1,
        },
    ]

    with patch(
        "app.ai.ollama_service.engine.connect"
    ) as mock_connect:
        mock_connection = (
            mock_connect.return_value.__enter__.return_value
        )
        mock_connection.execute.return_value \
            .mappings.return_value.all.return_value = rows

        with pytest.raises(RuntimeError, match="Multiple active models"):
            get_active_model()


def test_get_active_model_fails_when_active_model_is_unapproved():
    row = {
        "model_id": 1,
        "model_name": "qwen2.5-coder",
        "version": "7b",
        "approved": 0,
    }

    with patch(
        "app.ai.ollama_service.engine.connect"
    ) as mock_connect:
        mock_connection = (
            mock_connect.return_value.__enter__.return_value
        )
        mock_connection.execute.return_value \
            .mappings.return_value.all.return_value = [row]

        with pytest.raises(RuntimeError, match="not approved"):
            get_active_model()


def test_update_model_latency_initial_value():
    from app.ai.ollama_service import update_model_latency

    fake_row = {
        "avg_latency_ms": None,
        "latency_sample_count": 0,
    }

    with patch("app.ai.ollama_service.engine.begin") as mock_begin:
        db = mock_begin.return_value.__enter__.return_value
        db.execute.return_value.mappings.return_value.first.return_value = fake_row

        update_model_latency("qwen2.5-coder:7b", 120.50)

        calls = db.execute.call_args_list
        assert len(calls) == 2

        params = calls[1].args[1]
        assert params["latency"] == 120
        assert params["sample_count"] == 1


def test_update_model_latency_running_average():
    from app.ai.ollama_service import update_model_latency

    fake_row = {
        "avg_latency_ms": 100,
        "latency_sample_count": 1,
    }

    with patch("app.ai.ollama_service.engine.begin") as mock_begin:
        db = mock_begin.return_value.__enter__.return_value
        db.execute.return_value.mappings.return_value.first.return_value = fake_row

        update_model_latency("qwen2.5-coder:7b", 200)

        calls = db.execute.call_args_list
        params = calls[1].args[1]

        assert params["latency"] == 150
        assert params["sample_count"] == 2

def test_generate_sql_records_model_latency():
    from app.ai.ollama_service import generate_sql

    fake_response = type(
        "FakeResponse",
        (),
        {
            "raise_for_status": lambda self: None,
            "json": lambda self: {
                "response": "SELECT employee_id FROM employees"
            },
        },
    )()

    with patch(
        "app.ai.ollama_service.build_schema_context",
        return_value="employees(employee_id)",
    ), patch(
        "app.ai.ollama_service.get_active_model",
        return_value="qwen2.5-coder:7b",
    ), patch(
        "app.ai.ollama_service.requests.post",
        return_value=fake_response,
    ), patch(
        "app.ai.ollama_service.update_model_latency"
    ) as mock_update:

        sql = generate_sql(
            "EMP002",
            "Show my employee ID",
        )

    assert sql == "SELECT employee_id FROM employees"

    mock_update.assert_called_once()

    args = mock_update.call_args.args

    assert args[0] == "qwen2.5-coder:7b"
    assert args[1] >= 0

def test_update_model_latency_average_across_three_samples():
    from app.ai.ollama_service import update_model_latency

    fake_row = {
        "avg_latency_ms": 150,
        "latency_sample_count": 2,
    }

    with patch("app.ai.ollama_service.engine.begin") as mock_begin:
        db = mock_begin.return_value.__enter__.return_value
        db.execute.return_value.mappings.return_value.first.return_value = fake_row

        update_model_latency("qwen2.5-coder:7b", 300)

        params = db.execute.call_args_list[1].args[1]

        assert params["latency"] == 200
        assert params["sample_count"] == 3