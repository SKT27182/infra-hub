"""User management router (SUPER_ADMIN only)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from config import settings
from services.auth import get_current_user, require_super_admin
from services.user_db import InfraUserRole, user_service
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None
    role: str = Field(default=InfraUserRole.USER.value, pattern="^USER$")


class UserUpdateRequest(BaseModel):
    name: str | None = None
    password: str | None = Field(default=None, min_length=8)
    role: str | None = Field(default=None, pattern="^USER$")
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: Any
    updated_at: Any


@router.get("", response_model=list[UserResponse])
async def list_users(
    _: Annotated[dict[str, Any], Depends(require_super_admin)],
) -> list[dict[str, Any]]:
    return await user_service.list_users()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    _: Annotated[dict[str, Any], Depends(require_super_admin)],
) -> dict[str, Any]:
    user = await user_service.create_user(
        email=body.email,
        password=body.password,
        name=body.name,
        role=body.role,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    logger.info("Admin created user: %s", body.email)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdateRequest,
    current: Annotated[dict[str, Any], Depends(require_super_admin)],
) -> dict[str, Any]:
    existing = await user_service.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    if existing.get("role") == InfraUserRole.SUPER_ADMIN.value:
        if body.role is not None and body.role != InfraUserRole.SUPER_ADMIN.value:
            raise HTTPException(
                status_code=403,
                detail="Cannot demote SUPER_ADMIN via API",
            )
        if body.is_active is False:
            remaining = await user_service.count_super_admins(exclude_id=user_id)
            if remaining < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deactivate the last SUPER_ADMIN",
                )

    try:
        updated = await user_service.update_user(
            user_id,
            name=body.name,
            password=body.password,
            role=body.role,
            is_active=body.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Admin updated user id=%s", user_id)
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current: Annotated[dict[str, Any], Depends(require_super_admin)],
) -> None:
    if current.get("id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    existing = await user_service.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    if existing.get("role") == InfraUserRole.SUPER_ADMIN.value:
        remaining = await user_service.count_super_admins(exclude_id=user_id)
        if remaining < 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last SUPER_ADMIN",
            )

    if not await user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Admin deleted user id=%s", user_id)
