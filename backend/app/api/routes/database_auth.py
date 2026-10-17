from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database.connection import engine
from app.identity.identity_service import identity_service


router = APIRouter(
    prefix="/api/auth",
    tags=["Database Authentication"],
)


@router.get("/database/{employee_id}")
def database_auth(employee_id: str):
    """
    Authenticate database access using the server-resolved identity.

    The employee_id supplied by the client is treated only as an
    assertion and must match the authenticated server-side identity.
    """

    # --------------------------------------------------
    # 1. Resolve authenticated Windows identity
    # --------------------------------------------------

    identity = identity_service.resolve()

    if not identity:
        raise HTTPException(
            status_code=401,
            detail="Windows identity could not be verified",
        )

    authenticated_employee_id = identity["employee_id"]
    authenticated_role = identity["role"]

    # --------------------------------------------------
    # 2. Prevent Employee-ID spoofing
    # --------------------------------------------------

    if employee_id != authenticated_employee_id:
        raise HTTPException(
            status_code=403,
            detail="Employee ID does not match authenticated identity",
        )

    # --------------------------------------------------
    # 3. Verify database access using server-side identity
    # --------------------------------------------------

    with engine.connect() as db:

        user = db.execute(
            text(
                """
                SELECT
                    u.employee_id,
                    u.username,
                    r.role_name,
                    u.is_active
                FROM users u
                JOIN roles r
                    ON u.role_id = r.role_id
                WHERE u.employee_id = :employee_id
                """
            ),
            {
                "employee_id": authenticated_employee_id,
            },
        ).mappings().first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=403,
                detail="User account is inactive",
            )

        # --------------------------------------------------
        # 4. Verify role consistency
        # --------------------------------------------------

        if user["role_name"] != authenticated_role:
            raise HTTPException(
                status_code=403,
                detail="Authenticated role mismatch",
            )

        # --------------------------------------------------
        # 5. Verify query execution permission
        # --------------------------------------------------

        permission = db.execute(
            text(
                """
                SELECT 1
                FROM users u
                JOIN role_permissions rp
                    ON u.role_id = rp.role_id
                JOIN permissions p
                    ON rp.permission_id = p.permission_id
                WHERE u.employee_id = :employee_id
                  AND p.permission_name = 'execute_query'
                """
            ),
            {
                "employee_id": authenticated_employee_id,
            },
        ).first()

    if not permission:
        raise HTTPException(
            status_code=403,
            detail="Database access denied",
        )

    # --------------------------------------------------
    # 6. Return server-derived identity
    # --------------------------------------------------

    return {
        "authenticated": True,
        "employee_id": authenticated_employee_id,
        "username": user["username"],
        "role": authenticated_role,
        "database_access": True,
    }