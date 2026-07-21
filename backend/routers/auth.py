"""Infra Hub v2 login and logout endpoints."""

from collections import defaultdict, deque
from time import monotonic

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from config import settings
from services.auth import auth_service
from services.user_db import UserStoreUnavailableError, user_service

router = APIRouter(prefix="/auth", tags=["Auth"])
_attempts: dict[str, deque[float]] = defaultdict(deque)
_WINDOW_SECONDS = 300
_MAX_FAILURES = 5
_MAX_TRACKED_KEYS = 10_000


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _rate_keys(request: Request, email: str) -> tuple[str, str]:
    host = request.client.host if request.client else "local"
    return f"ip:{host}", f"email:{email.lower()}"


def _check_rate_limit(key: str) -> None:
    now = monotonic()
    attempts = _attempts[key]
    while attempts and attempts[0] < now - _WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= _MAX_FAILURES:
        raise HTTPException(status_code=429, detail="Too many login attempts")


@router.post("/login")
async def login(body: LoginRequest, request: Request, response: Response) -> dict[str, object]:
    """Authenticate and set a versioned HttpOnly session cookie."""
    keys = _rate_keys(request, body.email)
    for key in keys:
        _check_rate_limit(key)
    try:
        user = await user_service.get_user_by_email(body.email)
    except UserStoreUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Authentication store unavailable") from exc
    valid = bool(
        user
        and user.get("is_active", False)
        and auth_service.verify_password(body.password, user["hashed_password"])
    )
    if not valid:
        for key in keys:
            if len(_attempts) >= _MAX_TRACKED_KEYS and key not in _attempts:
                _attempts.pop(next(iter(_attempts)))
            _attempts[key].append(monotonic())
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    assert user is not None
    for key in keys:
        _attempts.pop(key, None)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=auth_service.create_session_token(user),
        max_age=settings.session_lifetime_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="strict",
        path="/api/v2",
    )
    return user_service.public_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear the v2 session cookie."""
    response.delete_cookie(settings.auth_cookie_name, path="/api/v2")
