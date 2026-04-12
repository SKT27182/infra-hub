"""
Authentication router handling login and signup.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from services.auth import auth_service
from services.user_db import user_service

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
    user = await user_service.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not auth_service.verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = auth_service.create_access_token(
        data={"sub": user["email"], "id": user["id"]}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
        },
    }
