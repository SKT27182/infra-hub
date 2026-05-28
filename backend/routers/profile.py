"""Current user profile endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from services.auth import auth_service, get_current_user
from services.user_db import user_service
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserMeResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: Any
    updated_at: Any


class ProfileUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    user = await user_service.get_user_by_id(current["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me/profile", response_model=UserMeResponse)
async def update_profile(
    body: ProfileUpdate,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    updated = await user_service.update_user(
        current["id"],
        name=body.name,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Profile updated for user id=%s", current["id"])
    return updated


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChange,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
) -> None:
    user = await user_service.get_user_by_email(current["email"])
    if not user or not auth_service.verify_password(
        body.current_password, user["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    updated = await user_service.update_user(
        current["id"],
        password=body.new_password,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Password changed for user id=%s", current["id"])
