"""
Authentication router handling login and signup.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from config import settings
from services.auth import auth_service
from services.user_db import UserStoreUnavailableError, user_service
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCreate(BaseModel):
    """Signup request schema."""

    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


"""
@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserCreate) -> dict[str, Any]:
...
    }
"""


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin) -> dict[str, Any]:
    """Login a user."""
    try:
        user = await user_service.get_user_by_email(login_data.email)
    except UserStoreUnavailableError as exc:
        logger.warning("Login unavailable: user database unreachable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is unavailable because the user database is unreachable.",
        ) from exc

    if not user:
        logger.debug("Login failed: unknown email")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.get("is_active", True):
        logger.warning("Login rejected: deactivated account for %s", login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    if not auth_service.verify_password(login_data.password, user["hashed_password"]):
        logger.debug("Login failed: invalid password for %s", login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    role = user.get("role", "USER")
    access_token = auth_service.create_access_token(
        data={"sub": user["email"], "id": user["id"], "role": role}
    )
    logger.info("User logged in: %s", login_data.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name") or user.get("full_name") or "User",
            "role": role,
            "is_active": user.get("is_active", True),
        },
    }
