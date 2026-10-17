from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database.connection import engine
from app.identity.identity_service import identity_service


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

admin_router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin Users"],
)


@router.get("/{employee_id}")
def get_user(employee_id: str):
    with engine.connect() as db:
        row = db.execute(
            text("""
                SELECT
                    u.employee_id,
                    u.username,
                    r.role_name,
                    u.is_active
                FROM users u
                JOIN roles r
                    ON u.role_id = r.role_id
                WHERE u.employee_id = :employee_id
            """),
            {"employee_id": employee_id},
        ).mappings().first()

    if not row:
        raise HTTPException(404, "User not found")

    return dict(row)


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


@admin_router.get("")
def get_admin_users(
    search: str | None = None,
    limit: int = 100,
):
    require_admin()

    limit = max(1, min(limit, 500))

    query = """
        SELECT
            u.employee_id,
            u.username,
            r.role_name,
            u.is_active
        FROM users u
        JOIN roles r
            ON u.role_id = r.role_id
    """

    params = {
        "limit": limit,
    }

    if search:
        query += """
            WHERE
                u.employee_id LIKE :search
                OR u.username LIKE :search
        """
        params["search"] = f"%{search}%"

    query += """
        ORDER BY u.employee_id
        LIMIT :limit
    """

    with engine.connect() as db:
        rows = db.execute(
            text(query),
            params,
        ).mappings().all()

    return {
        "success": True,
        "count": len(rows),
        "users": [dict(row) for row in rows],
    }