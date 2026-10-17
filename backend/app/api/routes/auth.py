from fastapi import APIRouter, HTTPException

from app.identity.identity_service import identity_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/me")
def current_user():
    identity = identity_service.resolve()

    if not identity:
        raise HTTPException(
            status_code=401,
            detail="Windows identity could not be verified",
        )

    return {
        "authenticated": True,
        **identity,
    }