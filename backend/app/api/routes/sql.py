from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.database.connection import engine
from app.security.sql_authorizer import authorize_sql

router = APIRouter(
    prefix="/api/sql",
    tags=["SQL Authorization"]
)


class SQLRequest(BaseModel):
    employee_id: str
    sql: str


@router.post("/authorize")
def authorize(request: SQLRequest):

    with engine.connect() as db:
        policy = db.execute(
            text("""
                SELECT p.allowed_columns, p.table_name
                FROM users u
                JOIN data_policies p
                    ON u.role_id = p.role_id
                WHERE u.employee_id = :employee_id
                  AND u.is_active = 1
            """),
            {"employee_id": request.employee_id}
        ).mappings().first()

    if not policy:
        return {
            "authorized": False,
            "reason": "No policy found",
            "authorized_sql": None
        }

    allowed_columns = set(
        policy["allowed_columns"].split(",")
    )

    allowed_tables = [
        policy["table_name"]
    ]

    ok, reason, authorized_sql = authorize_sql(
        request.sql,
        allowed_columns,
        allowed_tables
    )

    return {
        "authorized": ok,
        "reason": reason,
        "authorized_sql": authorized_sql
    }