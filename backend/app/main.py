from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.database import router as db_router
from app.api.routes.users import router as users_router, admin_router as admin_users_router
from app.api.routes.audit import router as admin_audit_router
from app.api.routes.models import router as admin_models_router
from app.api.routes.permissions import router as permissions_router
from app.api.routes.database_auth import router as database_auth_router
from app.api.routes.policy import router as policy_router
from app.api.routes.sql import router as sql_router
from app.api.routes.query import router as query_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes import security_events

app = FastAPI(title="QueryShield API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(db_router)
app.include_router(users_router)
app.include_router(admin_users_router)
app.include_router(admin_audit_router)
app.include_router(admin_models_router)
app.include_router(permissions_router)
app.include_router(database_auth_router)
app.include_router(policy_router)
app.include_router(sql_router)
app.include_router(query_router)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(alerts_router)
app.include_router(security_events.router)