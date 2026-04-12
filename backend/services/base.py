"""
Base service class - Abstract interface for all managed services.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from infra_docker import DockerClient


class ServiceStatus(BaseModel):
    """Service status model."""

    name: str
    display_name: str
    running: bool
    healthy: bool
    container_id: str | None = None
    container_name: str | None = None
    status: str = "unknown"
    ports: list[str] = []
    admin_url: str | None = None


class BaseService(ABC):
    """
    Abstract base class for all managed services.

    To add a new service:
    1. Create a new file in services/
    2. Inherit from BaseService
    3. Implement get_info
    4. Register in main.py lifespan handler
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

        # Health is derived purely from Docker health check if present, else running status
        health_info = container.attrs.get("State", {}).get("Health", {})
        if health_info:
            healthy = health_info.get("Status") == "healthy"
        else:
            healthy = running

        # Get ports
        ports = []
        port_bindings = container.attrs.get("NetworkSettings", {}).get("Ports", {})
        for container_port, bindings in port_bindings.items():
            if bindings:
                for binding in bindings:
                    host_port = binding.get("HostPort", "")
                    if host_port:
                        ports.append(f"{host_port}:{container_port}")

        return ServiceStatus(
            name=self.name,
            display_name=self.display_name,
            running=running,
            healthy=healthy,
            container_id=container.short_id,
            container_name=self.container_name,
            status=status,
            ports=ports,
            admin_url=self.admin_url,
        )

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
