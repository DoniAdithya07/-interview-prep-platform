from fastapi import APIRouter, Depends

from backend.app.core.dependencies import get_current_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
def current_user(user: dict = Depends(get_current_user)) -> dict:
    return user

