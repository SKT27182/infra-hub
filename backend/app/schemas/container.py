"""
Container-related Pydantic schemas.
"""

from pydantic import BaseModel


class ContainerInfo(BaseModel):
    """Container information model."""

    id: str
    name: str
    image: str
    status: str
    state: str
    created: str | None = None
    ports: list[str] = []
    labels: dict[str, str] = {}


class ContainerStats(BaseModel):
    """Container resource statistics."""

    container_id: str
    cpu_percent: float | None = None
    memory_usage: int | None = None
    memory_limit: int | None = None
    memory_percent: float | None = None
    network_rx: int | None = None
    network_tx: int | None = None


class ContainerAction(BaseModel):
    """Container action response."""

    success: bool
    message: str
    container_id: str


class ContainerLogs(BaseModel):
    """Container logs response."""

    container_id: str
    logs: str
    lines: int
