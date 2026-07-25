"""Critical v2 authentication and route-boundary tests."""

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.testclient import TestClient
from pydantic import ValidationError

from config import Settings
from main import OriginGuardMiddleware, RequestSizeLimitMiddleware
from routers import auth as auth_router
from services import auth as auth_module
from services import user_db as user_db_module
from services.auth import auth_service


def test_session_token_contains_versioned_required_claims() -> None:
    token = auth_service.create_session_token(
        {"id": 7, "email": "admin@example.test", "auth_version": 3}
    )

    payload = auth_service.decode_session_token(token)

    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["email"] == "admin@example.test"
    assert payload["ver"] == 3
    assert all(payload.get(claim) for claim in ("iss", "aud", "iat", "nbf", "exp", "jti"))


def test_v1_and_user_management_routes_are_absent() -> None:
    from main import app

    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/api/users" not in paths
    assert "/api/v2/users" not in paths
    assert not any(path.startswith("/api/") and not path.startswith("/api/v2/") for path in paths)
    assert "/api/v2/auth/signup" not in paths

    client = TestClient(app)
    assert client.get("/api/v2/health/live").status_code == 200
    assert client.get("/api/health/live").status_code == 404
    assert client.get("/api/v2/services").status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("user", [None, {"id": 7, "email": "admin@example.test", "auth_version": 0, "is_active": False}])
async def test_missing_and_inactive_users_are_rejected(
    monkeypatch: pytest.MonkeyPatch, user: dict[str, Any] | None
) -> None:
    token = auth_service.create_session_token(
        {"id": 7, "email": "admin@example.test", "auth_version": 0}
    )

    async def get_user(_: str) -> dict[str, Any] | None:
        return user

    monkeypatch.setattr(user_db_module.user_service, "get_user_by_email", get_user)

    with pytest.raises(HTTPException) as caught:
        await auth_module.get_current_user(token)

    assert caught.value.status_code == 401


def test_password_change_sql_increments_auth_version() -> None:
    source = Path("services/user_db.py").read_text(encoding="utf-8")
    assert "auth_version = auth_version + 1" in source


def test_wildcard_bind_is_rejected_in_host_only_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    with pytest.raises(ValidationError, match="loopback"):
        Settings()  # type: ignore[call-arg]


def test_short_signing_secret_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(ValidationError, match="32 bytes"):
        Settings()  # type: ignore[call-arg]


def test_postgres_defaults_to_ipv4_loopback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POSTGRES_HOST", raising=False)

    configured = Settings()  # type: ignore[call-arg]

    assert configured.postgres_host == "127.0.0.1"
    assert "@127.0.0.1:" in configured.postgres_url


@pytest.mark.asyncio
async def test_login_sets_strict_httponly_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    user = {
        "id": 7,
        "email": "admin@example.test",
        "name": "Admin",
        "is_active": True,
        "auth_version": 0,
        "hashed_password": "hash",
    }

    async def get_user(_: str) -> dict[str, Any]:
        return user

    monkeypatch.setattr(user_db_module.user_service, "get_user_by_email", get_user)
    monkeypatch.setattr(auth_module.auth_service, "verify_password", lambda plain, hashed: True)
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v2/auth/login",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
    )
    response = Response()

    result = await auth_router.login(
        auth_router.LoginRequest(email="admin@example.com", password="valid-password"),
        request,
        response,
    )

    cookie = response.headers["set-cookie"].lower()
    assert result["email"] == "admin@example.test"
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "path=/api/v2" in cookie


def test_request_body_limit_and_cookie_origin_guard() -> None:
    test_app = FastAPI()
    test_app.add_middleware(OriginGuardMiddleware)
    test_app.add_middleware(RequestSizeLimitMiddleware)

    @test_app.post("/mutation")
    async def mutation(request: Request) -> dict[str, bool]:
        await request.body()
        return {"ok": True}

    client = TestClient(test_app)
    oversized = client.post(
        "/mutation",
        content=b"x" * (1024 * 1024 + 1),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert oversized.status_code == 413
    assert oversized.json()["error"]["code"] == "request_too_large"

    client.cookies.set("infra_hub_session", "signed-value")
    forbidden = client.post("/mutation")
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "origin_forbidden"
