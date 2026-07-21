"""Current infra-admin profile endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator

from config import settings
from services.auth import auth_service, get_current_user
from services.user_db import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Reject blank display names after normalization."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name cannot be blank")
        return normalized


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=256)

    @field_validator("new_password")
    @classmethod
    def validate_bcrypt_length(cls, value: str) -> str:
        """Enforce bcrypt's byte limit before hashing."""
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


@router.get("/me")
async def get_me(current: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
    return current


@router.patch("/me/profile")
async def update_profile(
    body: ProfileUpdate,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    updated = await user_service.update_profile(current["id"], body.name)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChange,
    response: Response,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
) -> None:
    user = await user_service.get_user_by_email(current["email"])
    if not user or not auth_service.verify_password(body.current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    changed = await user_service.change_password(
        current["id"], auth_service.get_password_hash(body.new_password)
    )
    if not changed:
        raise HTTPException(status_code=404, detail="User not found")
    response.delete_cookie(settings.auth_cookie_name, path="/api/v2")
