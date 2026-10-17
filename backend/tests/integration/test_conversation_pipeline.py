from app.conversation.conversation_service import ConversationService


def test_conversation_context_belongs_to_authenticated_employee():
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

    context = service.get_context(
        conversation_id,
        "EMP001",
        "Admin",
    )

    assert len(context) == 1
    assert context[0]["content"] == "Show my department"


def test_conversation_cannot_cross_employee_boundary():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    try:
        service.get_context(
            conversation_id,
            "EMP002",
            "Employee",
        )
        assert False, "Cross-employee conversation access was allowed"
    except PermissionError:
        pass


def test_conversation_cannot_cross_role_boundary():
    service = ConversationService()

    conversation_id = service.create_conversation(
        employee_id="EMP001",
        role="Admin",
    )

    try:
        service.get_context(
            conversation_id,
            "EMP001",
            "Employee",
        )
        assert False, "Cross-role conversation access was allowed"
    except PermissionError:
        pass