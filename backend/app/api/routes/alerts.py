
from fastapi import APIRouter, Depends, HTTPException

from app.identity.identity_service import identity_service
from app.monitoring.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


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
def alerts(_admin=Depends(require_admin)):
    return alert_service.list_alerts()


@router.get("/active")
def active_alerts(_admin=Depends(require_admin)):
    return alert_service.list_alerts(unresolved_only=True)


@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    _admin=Depends(require_admin),
):
    alert = alert_service.resolve(alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert