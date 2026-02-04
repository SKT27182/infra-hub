"""
Service-related Pydantic schemas.
"""

from typing import Any

from pydantic import BaseModel


class ServiceStatusResponse(BaseModel):
    """Service status response."""

    name: str
    display_name: str
    running: bool
    healthy: bool
    container_id: str | None = None
    container_name: str | None = None
    status: str = "unknown"
    uptime: str | None = None
    ports: list[str] = []
    admin_url: str | None = None


class ServiceHealthResponse(BaseModel):
    """Service health check response."""

    healthy: bool
    message: str
    details: dict[str, Any] = {}


class ServiceInfoResponse(BaseModel):
    """Service detailed information response."""

    name: str
    info: dict[str, Any]


class ServiceActionResponse(BaseModel):
    """Service action response."""

    success: bool
    message: str
    service: str


class AllServicesResponse(BaseModel):
    """All services status response."""

    services: list[ServiceStatusResponse]
    total: int
    healthy: int
    unhealthy: int
