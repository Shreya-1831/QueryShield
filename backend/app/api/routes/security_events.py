from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database.connection import engine
from app.identity.identity_service import identity_service


router = APIRouter(
    prefix="/api/admin/security-events",
    tags=["Admin Security Events"],
)


def require_admin():
    identity = identity_service.resolve()

    if not identity:
        raise HTTPException(
            status_code=401,
            detail="Windows identity could not be verified",
        )

    if identity.get("role") != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return identity


@router.get("")
def get_security_events(
    unresolved_only: bool = False,
    limit: int = 50,
):
    require_admin()

    # Keep responses small and bounded.
    limit = max(1, min(limit, 100))

    query = """
        SELECT
            event_id,
            user_id,
            event_type,
            severity,
            details,
            created_at,
            resolved_at
        FROM security_events
    """

    params = {"limit": limit}

    if unresolved_only:
        query += " WHERE resolved_at IS NULL"

    query += """
        ORDER BY created_at DESC, event_id DESC
        LIMIT :limit
    """

    with engine.connect() as db:
        rows = db.execute(
            text(query),
            params,
        ).mappings().all()

    events = [dict(row) for row in rows]

    # Convert datetime values to JSON-safe strings.
    for event in events:
        for field in ("created_at", "resolved_at"):
            value = event.get(field)
            if value is not None:
                event[field] = value.isoformat()

    return {
        "success": True,
        "count": len(events),
        "events": events,
    }


@router.post("/{event_id}/resolve")
def resolve_security_event(event_id: int):
    require_admin()

    with engine.begin() as db:
        result = db.execute(
            text("""
                UPDATE security_events
                SET resolved_at = NOW()
                WHERE event_id = :event_id
                  AND resolved_at IS NULL
            """),
            {"event_id": event_id},
        )

        if result.rowcount == 0:
            exists = db.execute(
                text("""
                    SELECT event_id
                    FROM security_events
                    WHERE event_id = :event_id
                """),
                {"event_id": event_id},
            ).first()

            if not exists:
                raise HTTPException(
                    status_code=404,
                    detail="Security event not found",
                )

            raise HTTPException(
                status_code=409,
                detail="Security event is already resolved",
            )

    return {
        "success": True,
        "event_id": event_id,
        "resolved": True,
    }