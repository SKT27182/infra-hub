"""
Docker client wrapper for container management.
"""

from typing import Any

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container


class DockerClient:
    """Singleton Docker client wrapper."""

    _client: docker.DockerClient | None = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize Docker client."""
        try:
            cls._client = docker.from_env()
            cls._client.ping()
        except DockerException as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}") from e

    @classmethod
    def close(cls) -> None:
        """Close Docker client."""
        if cls._client:
            cls._client.close()
            cls._client = None

    @classmethod
    def get_client(cls) -> docker.DockerClient:
        """Get Docker client instance."""
        if cls._client is None:
            cls.initialize()
        return cls._client  # type: ignore

    @classmethod
    def list_containers(cls, all: bool = True) -> list[Container]:
        """List all containers."""
        return cls.get_client().containers.list(all=all)

    @classmethod
    def get_container(cls, container_id: str) -> Container | None:
        """Get container by ID or name."""
        try:
            return cls.get_client().containers.get(container_id)
        except NotFound:
            return None

    @classmethod
    def get_container_stats(cls, container_id: str) -> dict[str, Any]:
        """Get container resource stats."""
        container = cls.get_container(container_id)
        if container is None:
            return {}
        try:
            return container.stats(stream=False)
        except Exception:
            return {}

    @classmethod
    def start_container(cls, container_id: str) -> bool:
        """Start a container."""
        container = cls.get_container(container_id)
        if container is None:
            return False
        try:
            container.start()
            return True
        except Exception:
            return False

    @classmethod
    def stop_container(cls, container_id: str) -> bool:
        """Stop a container."""
        container = cls.get_container(container_id)
        if container is None:
            return False
        try:
            container.stop()
            return True
        except Exception:
            return False

    @classmethod
    def restart_container(cls, container_id: str) -> bool:
        """Restart a container."""
        container = cls.get_container(container_id)
        if container is None:
            return False
        try:
            container.restart()
            return True
        except Exception:
            return False

    @classmethod
    def get_container_logs(
        cls, container_id: str, tail: int = 100, since: int | None = None
    ) -> str:
        """Get container logs."""
        container = cls.get_container(container_id)
        if container is None:
            return ""
        try:
            logs = container.logs(tail=tail, since=since, timestamps=True)
            return logs.decode("utf-8") if isinstance(logs, bytes) else str(logs)
        except Exception:
            return ""
