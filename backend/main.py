"""Infra Hub v2 FastAPI application."""

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from config import settings
from infra_docker import DockerClient
from routers import auth, health, profile, services
from services.auth import auth_service
from services.user_db import UserStoreUnavailableError, user_service
from utils.logger import create_logger
from utils.logging_bridge import configure_third_party_loggers, setup_unified_logging

logger = create_logger(__name__, level=settings.log_level)
setup_unified_logging(settings.log_level)
security = HTTPBasic()


class RequestBodyTooLarge(Exception):
    """Raised while consuming a request that exceeds the configured ceiling."""


class RequestSizeLimitMiddleware:
    """Enforce the request-body ceiling even for chunked HTTP requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        consumed = 0
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")

        async def reject() -> None:
            request_id = str(uuid4())
            response = JSONResponse(
                status_code=413,
                content={"error": {"code": "request_too_large", "message": "Request body exceeds 1 MiB", "request_id": request_id}},
            )
            await response(scope, receive, send)

        if content_length:
            try:
                if int(content_length) > settings.max_request_body_bytes:
                    await reject()
                    return
            except ValueError:
                await reject()
                return

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > settings.max_request_body_bytes:
                    raise RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestBodyTooLarge:
            await reject()
        except BaseExceptionGroup as exc:
            if exc.subgroup(RequestBodyTooLarge) is None:
                raise
            await reject()


class OriginGuardMiddleware(BaseHTTPMiddleware):
    """Reject cross-origin cookie-authenticated state changes."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        request_id = str(uuid4())
        request.state.request_id = request_id
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.cookies.get(
            settings.auth_cookie_name
        ):
            origin = request.headers.get("origin")
            if not origin or origin.rstrip("/") not in settings.cors_origins:
                return JSONResponse(
                    status_code=403,
                    content={"error": {"code": "origin_forbidden", "message": "Origin is not allowed", "request_id": request_id}},
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    configure_third_party_loggers(settings.log_level)
    DockerClient.initialize()
    await user_service.ensure_schema()
    await user_service.ensure_default_admin_user()
    yield
    DockerClient.close()


app = FastAPI(
    title="Infra Hub API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(OriginGuardMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    """Return the stable v2 error envelope."""
    messages = exc.detail if isinstance(exc.detail, str) else "Request failed"
    codes = {
        401: "authentication_required",
        403: "forbidden",
        404: "not_found",
        409: "invalid_transition",
        429: "rate_limited",
        502: "upstream_failure",
        503: "service_unavailable",
        504: "operation_timeout",
    }
    code = codes.get(exc.status_code, "request_failed")
    if request.url.path.startswith(("/api/v2/containers", "/api/v2/services")):
        if exc.status_code == 504:
            code = "container_timeout"
        elif exc.status_code == 502:
            code = "container_operation_failed"
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={"error": {"code": code, "message": messages, "request_id": request.state.request_id}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return validation failures without echoing request values."""
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "Request validation failed", "request_id": request.state.request_id}},
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures and return no internal exception details."""
    logger.exception(
        "Unhandled request failure request_id=%s type=%s",
        request.state.request_id,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "The request could not be completed", "request_id": request.state.request_id}},
    )


async def get_docs_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    try:
        user = await user_service.get_user_by_email(credentials.username)
    except UserStoreUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Documentation unavailable") from exc
    if (
        not user
        or not user.get("is_active", False)
        or not auth_service.verify_password(credentials.password, user["hashed_password"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return str(user["email"])


@app.get("/api/v2/docs", include_in_schema=False)
async def documentation(_: Annotated[str, Depends(get_docs_auth)]) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/api/v2/openapi.json", title="Infra Hub API v2"
    )


@app.get("/api/v2/openapi.json", include_in_schema=False)
async def openapi_schema(
    _: Annotated[str, Depends(get_docs_auth)],
) -> dict[str, Any]:
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.get("/api/v2/health/live", tags=["Health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


app.include_router(health.router, prefix="/api/v2", tags=["Health"])
app.include_router(services.router, prefix="/api/v2", tags=["Services"])
app.include_router(auth.router, prefix="/api/v2")
app.include_router(profile.router, prefix="/api/v2")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
