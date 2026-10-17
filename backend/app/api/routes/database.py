from fastapi import APIRouter
from app.database.connection import check_db

router = APIRouter(prefix="/api/db", tags=["Database"])

@router.get("/health")
def db_health():
    return {"status": "ok" if check_db() else "failed"}