"""
Base service class - Abstract interface for all managed services.
"""

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel

from config import settings
from infra_docker import DockerClient
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)


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
            logger.debug("Container not found for service %s", self.name)
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
        healthy = health_info.get("Status") == "healthy" if health_info else running

        if running and not healthy:
            logger.warning("Service %s running but unhealthy", self.name)

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

    async def action(
        self, action: Literal["start", "stop", "restart"]
    ) -> list[dict[str, Any]]:
        """Apply an action to the primary and optional admin container."""
        targets = [self.container_name]
        if self.admin_container:
            if action == "stop":
                targets.insert(0, self.admin_container)
            else:
                targets.append(self.admin_container)
        results: list[dict[str, Any]] = []
        failures: list[tuple[str, Exception]] = []
        for target in targets:
            try:
                results.append(
                    await DockerClient.perform_action(
                        target, action, allow_already_target=True
                    )
                )
            except (LookupError, RuntimeError, TimeoutError, ValueError) as exc:
                failures.append((target, exc))
        if failures:
            names = ", ".join(target for target, _ in failures)
            errors = [error for _, error in failures]
            if all(isinstance(error, ValueError) for error in errors):
                raise ValueError(f"Invalid container transition for: {names}")
            if any(isinstance(error, TimeoutError) for error in errors):
                raise TimeoutError(f"Container action timed out for: {names}")
            if all(isinstance(error, LookupError) for error in errors):
                raise LookupError(f"Infra Hub container not found: {names}")
            raise RuntimeError(f"Container action failed for: {names}")
        return results

    def get_logs(self, tail: int = 100) -> str:
        """Get service container logs."""
        return DockerClient.get_container_logs(self.container_name, tail=tail)
