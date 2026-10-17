from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database.connection import engine

router = APIRouter(prefix="/api/policy", tags=["Policy"])

@router.get("/{employee_id}/{table_name}")
def get_policy(employee_id: str, table_name: str):
    with engine.connect() as db:
        policy = db.execute(text("""
            SELECT r.role_name, p.table_name, p.allowed_columns, p.row_condition
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            JOIN data_policies p ON p.role_id = u.role_id
            WHERE u.employee_id = :employee_id
              AND u.is_active = 1
              AND p.table_name = :table_name
        """), {
            "employee_id": employee_id,
            "table_name": table_name
        }).mappings().first()

    if not policy:
        raise HTTPException(403, "Access denied")

    return dict(policy)