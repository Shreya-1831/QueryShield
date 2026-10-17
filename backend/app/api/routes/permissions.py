from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database.connection import engine

router = APIRouter(prefix="/api/permissions", tags=["Permissions"])

@router.get("/{employee_id}")
def get_permissions(employee_id: str):
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT p.permission_name
            FROM users u
            JOIN role_permissions rp ON u.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.permission_id
            WHERE u.employee_id = :employee_id AND u.is_active = 1
        """), {"employee_id": employee_id}).scalars().all()

    if not rows:
        raise HTTPException(404, "User not found or inactive")

    return {"employee_id": employee_id, "permissions": rows}