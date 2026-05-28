"""
Authentication service handling JWT and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from config import settings
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization helper."""

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
            return payload
        except (jwt.PyJWTError, Exception):
            logger.debug("JWT decode failed")
            return None


auth_service = AuthService()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Dependency to get the current authenticated user."""
    from services.user_db import UserStoreUnavailableError, user_service

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth_service.decode_token(token)
    if payload is None:
        logger.debug("Auth rejected: invalid token")
        raise credentials_exception
    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    try:
        user = await user_service.get_user_by_email(email)
    except UserStoreUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User database is unavailable",
        ) from exc

    if not user or not user.get("is_active", True):
        logger.debug("Auth rejected: user missing or inactive for %s", email)
        raise credentials_exception

    name = user.get("name") or user.get("full_name")
    if not name:
        email = user.get("email") or ""
        name = email.split("@", 1)[0] if email else "User"
    return {
        "id": user["id"],
        "email": user["email"],
        "name": name,
        "role": user.get("role", "USER"),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


async def require_super_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Require SUPER_ADMIN role."""
    if current_user.get("role") != "SUPER_ADMIN":
        logger.warning(
            "Super admin required, denied for user id=%s",
            current_user.get("id"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required",
        )
    return current_user
