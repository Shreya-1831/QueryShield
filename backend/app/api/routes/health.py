from fastapi import APIRouter
from app.monitoring.health_service import health_service
from app.monitoring.alert_service import alert_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health():
    result = health_service.all()
    alert_service.check_health(result)
    return result


@router.get("/database")
def database():
    return health_service.database()


@router.get("/ollama")
def ollama():
    return health_service.ollama()


@router.get("/system")
def system():
    return health_service.system()


@router.get("/gpu")
def gpu():
    return health_service.gpu()