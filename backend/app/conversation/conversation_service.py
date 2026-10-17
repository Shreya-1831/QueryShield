from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ConversationMessage:
    role: str
    content: str
    timestamp: str


@dataclass
class Conversation:
    conversation_id: str
    employee_id: str
    role: str
    messages: list[ConversationMessage] = field(default_factory=list)


class ConversationService:

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self._conversations: dict[str, Conversation] = {}

    # ---------------------------------------------------------
    # Create conversation
    # ---------------------------------------------------------
    def create_conversation(
        self,
        employee_id: str,
        role: str,
    ) -> str:

        conversation_id = str(uuid4())

        self._conversations[conversation_id] = Conversation(
            conversation_id=conversation_id,
            employee_id=employee_id,
            role=role,
        )

        return conversation_id

    # ---------------------------------------------------------
    # Validate conversation ownership
    # ---------------------------------------------------------
    def _get_conversation(
        self,
        conversation_id: str,
        employee_id: str,
        role: str,
    ) -> Conversation:

        conversation = self._conversations.get(conversation_id)

        if conversation is None:
            raise ValueError("Conversation not found")

        # Conversation context must belong to the
        # authenticated employee.
        if conversation.employee_id != employee_id:
            raise PermissionError(
                "Conversation does not belong to authenticated employee"
            )

        # Role must remain consistent with the
        # authenticated identity.
        if conversation.role != role:
            raise PermissionError(
                "Conversation role does not match authenticated role"
            )

        return conversation

    # ---------------------------------------------------------
    # Add message
    # ---------------------------------------------------------
    def add_message(
        self,
        conversation_id: str,
        employee_id: str,
        role: str,
        message_role: str,
        content: str,
    ) -> None:

        conversation = self._get_conversation(
            conversation_id,
            employee_id,
            role,
        )

        if message_role not in {"user", "assistant"}:
            raise ValueError("Invalid conversation message role")

        if not content or not content.strip():
            raise ValueError("Conversation message cannot be empty")

        timestamp = datetime.now(timezone.utc).isoformat()

        conversation.messages.append(
            ConversationMessage(
                role=message_role,
                content=content.strip(),
                timestamp=timestamp,
            )
        )

        # Keep only the most recent messages.
        conversation.messages = conversation.messages[
            -self.max_messages:
        ]

    # ---------------------------------------------------------
    # Get controlled context
    # ---------------------------------------------------------
    def get_context(
        self,
        conversation_id: str,
        employee_id: str,
        role: str,
    ) -> list[dict]:

        conversation = self._get_conversation(
            conversation_id,
            employee_id,
            role,
        )

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in conversation.messages
        ]

    # ---------------------------------------------------------
    # Get conversation
    # ---------------------------------------------------------
    def get_conversation(
        self,
        conversation_id: str,
        employee_id: str,
        role: str,
    ) -> Conversation:

        return self._get_conversation(
            conversation_id,
            employee_id,
            role,
        )

    # ---------------------------------------------------------
    # Delete conversation
    # ---------------------------------------------------------
    def delete_conversation(
        self,
        conversation_id: str,
        employee_id: str,
        role: str,
    ) -> None:

        self._get_conversation(
            conversation_id,
            employee_id,
            role,
        )

        del self._conversations[conversation_id]

    
    def list_conversations(
        self,
        employee_id: str,
        role: str,
    ) -> list[dict]:
        """List conversations belonging to the authenticated employee."""
        items = []

        for conversation in self._conversations.values():
            # Never expose another employee's conversations.
            if conversation.employee_id != employee_id:
                continue

            # Do not expose conversations associated with a different role.
            if conversation.role != role:
                continue

            last_message = (
                conversation.messages[-1]
                if conversation.messages
                else None
            )

            items.append({
                "conversation_id": conversation.conversation_id,
                "message_count": len(conversation.messages),
                "last_message_at": (
                    last_message.timestamp if last_message else None
                ),
                "last_message": (
                    last_message.content if last_message else None
                ),
            })

        items.sort(
            key=lambda item: item["last_message_at"] or "",
            reverse=True,
        )

        return items

conversation_service = ConversationService()