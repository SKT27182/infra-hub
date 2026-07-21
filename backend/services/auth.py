"""Cookie-based authentication for the Infra Hub v2 API."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Cookie, HTTPException, status

from config import settings
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)


class AuthService:
    """Create and validate password hashes and versioned session tokens."""

    @staticmethod
    def get_password_hash(password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
            "ascii"
        )

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("ascii")
            )
        except (ValueError, UnicodeError):
            return False

    @staticmethod
    def create_session_token(user: dict[str, Any]) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user["id"]),
            "email": user["email"],
            "ver": int(user.get("auth_version", 0)),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=settings.session_lifetime_minutes),
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    @staticmethod
    def decode_session_token(token: str) -> dict[str, Any] | None:
        try:
            return jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options={"require": ["sub", "email", "ver", "iat", "nbf", "exp", "jti"]},
            )
        except jwt.PyJWTError:
            return None


auth_service = AuthService()


async def get_current_user(
    session_token: Annotated[str | None, Cookie(alias=settings.auth_cookie_name)] = None,
) -> dict[str, Any]:
    """Resolve an active user from the signed HttpOnly session cookie."""
    from services.user_db import UserStoreUnavailableError, user_service

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )
    if not session_token:
        raise unauthorized
    payload = auth_service.decode_session_token(session_token)
    if not payload:
        raise unauthorized
    try:
        user = await user_service.get_user_by_email(str(payload["email"]))
    except UserStoreUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Authentication store unavailable") from exc
    if (
        not user
        or not user.get("is_active", False)
        or str(user["id"]) != str(payload["sub"])
        or int(user.get("auth_version", 0)) != int(payload["ver"])
    ):
        raise unauthorized
    return user_service.public_user(user)
