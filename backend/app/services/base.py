"""
Base service class - Abstract interface for all managed services.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.core.docker import DockerClient


class ServiceStatus(BaseModel):
    """Service status model."""

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


class ServiceHealth(BaseModel):
    """Service health check result."""

    healthy: bool
    message: str
    details: dict[str, Any] = {}


class BaseService(ABC):
    """
    Abstract base class for all managed services.

    To add a new service:
    1. Create a new file in app/services/
    2. Inherit from BaseService
    3. Implement all abstract methods
    4. Register in app/main.py lifespan handler
    """

    # Service identification
    name: str  # Unique identifier (e.g., "postgres")
    display_name: str  # Human-readable name (e.g., "PostgreSQL")
    container_name: str  # Docker container name (e.g., "infra-postgres")

    # Admin UI configuration
    admin_url: str | None = None  # URL to admin interface
    admin_container: str | None = None  # Admin UI container name

    def get_status(self) -> ServiceStatus:
        """Get current service status from Docker."""
        container = DockerClient.get_container(self.container_name)

        if container is None:
            return ServiceStatus(
                name=self.name,
                display_name=self.display_name,
                running=False,
                healthy=False,
                status="not_found",
                admin_url=self.admin_url,
            )

        # Parse container status
        status = container.status
        running = status == "running"

        # Check health if available
        health = container.attrs.get("State", {}).get("Health", {})
        healthy = health.get("Status") == "healthy" if health else running

        # Get ports
        ports = []
        port_bindings = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        for container_port, bindings in port_bindings.items():
            if bindings:
                for binding in bindings:
                    host_port = binding.get("HostPort", "")
                    if host_port:
                        ports.append(f"{host_port}:{container_port}")

        # Calculate uptime
        uptime = None
        if running:
            started_at = container.attrs.get("State", {}).get("StartedAt")
            if started_at:
                uptime = started_at

        return ServiceStatus(
            name=self.name,
            display_name=self.display_name,
            running=running,
            healthy=healthy,
            container_id=container.short_id,
            container_name=self.container_name,
            status=status,
            uptime=uptime,
            ports=ports,
            admin_url=self.admin_url,
        )

    @abstractmethod
    async def check_health(self) -> ServiceHealth:
        """
        Perform a service-level health check.
        This should connect to the service and verify it's responding.
        """
        pass

    @abstractmethod
    async def get_info(self) -> dict[str, Any]:
        """
        Get detailed service information.
        This should return service-specific metadata.
        """
        pass

    def start(self) -> bool:
        """Start the service container."""
        success = DockerClient.start_container(self.container_name)
        # Also start admin container if configured
        if success and self.admin_container:
            DockerClient.start_container(self.admin_container)
        return success

    def stop(self) -> bool:
        """Stop the service container."""
        # Stop admin container first if configured
        if self.admin_container:
            DockerClient.stop_container(self.admin_container)
        return DockerClient.stop_container(self.container_name)

    def restart(self) -> bool:
        """Restart the service container."""
        success = DockerClient.restart_container(self.container_name)
        # Also restart admin container if configured
        if success and self.admin_container:
            DockerClient.restart_container(self.admin_container)
        return success

    def get_logs(self, tail: int = 100) -> str:
        """Get service container logs."""
        return DockerClient.get_container_logs(self.container_name, tail=tail)
