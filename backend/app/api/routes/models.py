from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database.connection import engine
from app.identity.identity_service import identity_service
import requests

from app.ai.ollama_service import is_model_available

router = APIRouter(
    prefix="/api/admin/models",
    tags=["Admin Models"]
)


def require_admin():
    identity = identity_service.resolve()

    if not identity:
        raise HTTPException(
            status_code=401,
            detail="Windows identity could not be verified"
        )

    if identity.get("role") != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return identity


@router.get("")
def get_models():
    """
    Return registered models and their management status.
    Admin only.
    """

    require_admin()

    with engine.connect() as db:
        rows = db.execute(
            text("""
                SELECT
                    model_id,
                    model_name,
                    version,
                    status,
                    approved,
                    avg_latency_ms,
                    created_at
                FROM model_registry
                ORDER BY model_id
            """)
        ).mappings().all()

    return {
        "success": True,
        "count": len(rows),
        "models": [dict(row) for row in rows]
    }


@router.post("/select")
def select_model(model_id: int):
    """Select an approved model after verifying Ollama availability."""
    require_admin()

    # Read the candidate without holding a transaction during the
    # network request.
    with engine.connect() as db:
        model = db.execute(
            text("""
                SELECT model_id, model_name, version, approved
                FROM model_registry
                WHERE model_id = :model_id
            """),
            {"model_id": model_id},
        ).mappings().first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if not model["approved"]:
        raise HTTPException(status_code=403, detail="Model is not approved")

    model_tag = f"{model['model_name']}:{model['version']}"

    try:
        available = is_model_available(model_tag)
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable or returned an invalid response",
        ) from exc

    if not available:
        raise HTTPException(
            status_code=409,
            detail="Selected model is not installed in Ollama",
        )

    try:
        with engine.begin() as db:
            # Lock registry rows to coordinate model selections.
            db.execute(
                text("""
                    SELECT model_id
                    FROM model_registry
                    ORDER BY model_id
                    FOR UPDATE
                """)
            ).all()

            # Re-read the model because approval may have changed
            # during the Ollama availability check.
            model = db.execute(
                text("""
                    SELECT model_id, model_name, version, approved
                    FROM model_registry
                    WHERE model_id = :model_id
                    FOR UPDATE
                """),
                {"model_id": model_id},
            ).mappings().first()

            if not model:
                raise HTTPException(
                    status_code=404,
                    detail="Model not found",
                )

            if not model["approved"]:
                raise HTTPException(
                    status_code=403,
                    detail="Model is not approved",
                )

            # Ensure the candidate still matches the checked model tag.
            if f"{model['model_name']}:{model['version']}" != model_tag:
                raise HTTPException(
                    status_code=409,
                    detail="Model configuration changed; retry selection",
                )

            db.execute(
                text("""
                    UPDATE model_registry
                    SET status = 'AVAILABLE'
                    WHERE status = 'ACTIVE'
                """)
            )

            result = db.execute(
                text("""
                    UPDATE model_registry
                    SET status = 'ACTIVE'
                    WHERE model_id = :model_id
                      AND approved = TRUE
                """),
                {"model_id": model_id},
            )

            if result.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="Model selection could not be completed",
                )

            selected_model = {
                "model_id": model["model_id"],
                "model_name": model["model_name"],
                "version": model["version"],
                "status": "ACTIVE",
                "approved": bool(model["approved"]),
            }

    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Model selection conflicted with a database constraint. Please retry.",
        ) from exc

    return {
        "success": True,
        "message": "Model selected successfully",
        "model": selected_model,
    }
