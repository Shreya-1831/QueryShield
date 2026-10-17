from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

import logging
from app.query.query_service import execute_query
from app.identity.identity_service import identity_service
from app.audit.audit_service import audit_service
from app.conversation.conversation_service import conversation_service
from app.conversation.context_resolver import context_resolver

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["Query"])


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = Field(None, min_length=1, max_length=100)


class QueryResponse(BaseModel):
    success: bool
    stage: str | None = None
    reason: str | None = None
    safe_alternative: str | None = None
    response: str | None = None
    sql: str | None = None
    row_count: int | None = None
    data: list[dict] | None = None
    visualization: dict | None = None
    privacy: dict | None = None
    conversation_id: str | None = None


def get_identity():
    identity = identity_service.resolve()
    if not identity:
        raise HTTPException(401, "Windows identity could not be verified")
    return identity


@router.post("", response_model=QueryResponse)
def query(request: QueryRequest):
    identity = get_identity()
    try:
        return execute_query(
            identity["employee_id"],
            request.prompt,
            identity["role"],
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while processing query")
        raise HTTPException(
            status_code=500,
            detail="Query processing failed",
        )


@router.post("/conversation", response_model=QueryResponse)
def conversation_query(request: QueryRequest):
    identity = get_identity()
    employee_id, role = identity["employee_id"], identity["role"]

    try:
        conversation_id = request.conversation_id or \
            conversation_service.create_conversation(employee_id, role)

        context = conversation_service.get_context(
            conversation_id, employee_id, role
        )

        prompt = context_resolver.resolve(request.prompt, context)

        result = execute_query(employee_id, prompt, role)

        conversation_service.add_message(
            conversation_id, employee_id, role, "user", request.prompt
        )

        assistant_content = (
            str(result.get("data", result))
            if result.get("success")
            else str(result.get("reason", "Query was not processed."))
        )

        conversation_service.add_message(
            conversation_id,
            employee_id,
            role,
            "assistant",
            assistant_content,
        )

        result["conversation_id"] = conversation_id
        return result

    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception:
        raise HTTPException(500, "Conversation query processing failed")


@router.get("/history")
def query_history():
    identity = get_identity()

    try:
        items = audit_service.get_query_history(
            employee_id=identity["employee_id"],
            role=identity["role"],
        )
        return {"items": items}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to retrieve query history")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve query history",
        )
