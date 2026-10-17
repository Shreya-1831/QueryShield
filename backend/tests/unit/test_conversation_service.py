import pytest

from app.conversation.conversation_service import (
    ConversationService,
)


def test_create_conversation():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    assert conversation_id
    assert conversation_id in service._conversations


def test_add_and_get_context():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    service.add_message(
        conversation_id,
        "EMP001",
        "Admin",
        "user",
        "Show my department",
    )

    service.add_message(
        conversation_id,
        "EMP001",
        "Admin",
        "assistant",
        "Your department is IT.",
    )

    context = service.get_context(
        conversation_id,
        "EMP001",
        "Admin",
    )

    assert len(context) == 2
    assert context[0]["role"] == "user"
    assert context[0]["content"] == "Show my department"
    assert context[1]["role"] == "assistant"


def test_conversation_cannot_be_accessed_by_another_employee():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    with pytest.raises(PermissionError):
        service.get_context(
            conversation_id,
            "EMP002",
            "Employee",
        )


def test_conversation_role_mismatch_is_blocked():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    with pytest.raises(PermissionError):
        service.get_context(
            conversation_id,
            "EMP001",
            "Employee",
        )


def test_context_is_limited():
    service = ConversationService(max_messages=3)

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    for i in range(5):
        service.add_message(
            conversation_id,
            "EMP001",
            "Admin",
            "user",
            f"Question {i}",
        )

    context = service.get_context(
        conversation_id,
        "EMP001",
        "Admin",
    )

    assert len(context) == 3
    assert context[0]["content"] == "Question 2"
    assert context[-1]["content"] == "Question 4"


def test_empty_message_is_rejected():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    with pytest.raises(ValueError):
        service.add_message(
            conversation_id,
            "EMP001",
            "Admin",
            "user",
            "   ",
        )