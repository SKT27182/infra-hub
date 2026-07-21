"""
Docker client wrapper for container management.
"""

import asyncio
from typing import Any, Literal

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from config import settings
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)


class DockerClient:
    """Singleton Docker client wrapper."""

    _client: docker.DockerClient | None = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize Docker client."""
        try:
            cls._client = docker.from_env(
                timeout=settings.service_request_timeout_seconds
            )
            cls._client.ping()
            logger.info("Docker daemon connected")
        except DockerException as e:
            logger.error("Failed to connect to Docker (%s)", type(e).__name__)
            raise RuntimeError("Failed to connect to Docker") from e

    @classmethod
    def close(cls) -> None:
        """Close Docker client."""
        if cls._client:
            cls._client.close()
            cls._client = None
            logger.verbose("Docker client closed")

    @classmethod
    def get_client(cls) -> docker.DockerClient:
        """Get Docker client instance."""
        if cls._client is None:
            cls.initialize()
        return cls._client

    @classmethod
    def list_containers(cls, all: bool = True) -> list[Container]:
        """List only containers declared in the Infra Hub registry."""
        containers = cls.get_client().containers.list(all=all)
        allowed = cls.allowed_container_names()
        return [container for container in containers if container.name in allowed]

    @classmethod
    def get_container(cls, container_id: str) -> Container | None:
        """Get container by ID or name."""
        try:
            return cls.get_client().containers.get(container_id)
        except NotFound:
            logger.debug("Container not found: %s", container_id)
            return None

    @classmethod
    def allowed_container_names(cls) -> set[str]:
        """Return the exact containers controlled by Infra Hub."""
        return {
            settings.postgres_container_name,
            settings.pgadmin_container_name,
            settings.redis_container_name,
            settings.redisinsight_container_name,
            settings.mongodb_container_name,
            settings.mongo_express_container_name,
            settings.qdrant_container_name,
            settings.minio_container_name,
            settings.neo4j_container_name,
            settings.opensearch_container_name,
            settings.opensearch_dashboards_container_name,
        }

    @classmethod
    def service_name_for_container(cls, container_name: str) -> str:
        """Resolve a managed primary/admin container to its service key."""
        mappings = {
            settings.postgres_container_name: settings.postgres_service_name,
            settings.pgadmin_container_name: settings.postgres_service_name,
            settings.redis_container_name: settings.redis_service_name,
            settings.redisinsight_container_name: settings.redis_service_name,
            settings.mongodb_container_name: settings.mongodb_service_name,
            settings.mongo_express_container_name: settings.mongodb_service_name,
            settings.qdrant_container_name: settings.qdrant_service_name,
            settings.minio_container_name: settings.minio_service_name,
            settings.neo4j_container_name: settings.neo4j_service_name,
            settings.opensearch_container_name: settings.opensearch_service_name,
            settings.opensearch_dashboards_container_name: settings.opensearch_service_name,
        }
        return mappings[container_name]

    @classmethod
    async def perform_action(
        cls,
        container_id: str,
        action: Literal["start", "stop", "restart"],
        timeout: float = 30.0,
        allow_already_target: bool = False,
    ) -> dict[str, Any]:
        """Run a Docker action and wait for its observable postcondition."""
        try:
            container = await asyncio.to_thread(cls.get_container, container_id)
        except DockerException as exc:
            raise RuntimeError("Docker operation failed") from exc
        if container is None or container.name not in cls.allowed_container_names():
            raise LookupError("Infra Hub container not found")
        before_started = container.attrs.get("State", {}).get("StartedAt")
        before_running = bool(container.attrs.get("State", {}).get("Running"))
        already_target = (action == "start" and before_running) or (
            action == "stop" and not before_running
        )
        if already_target and allow_already_target:
            state = container.attrs.get("State", {})
            health = state.get("Health", {}).get("Status")
            return {
                "name": container.name,
                "state": state.get("Status", "unknown"),
                "healthy": health == "healthy" if health else before_running,
                "health": health or ("running" if before_running else "none"),
            }
        if already_target or (action == "restart" and not before_running):
            raise ValueError("Container is already in an incompatible state")
        try:
            await asyncio.to_thread(getattr(container, action))
        except DockerException as exc:
            raise RuntimeError("Docker operation failed") from exc

        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.to_thread(container.reload)
            state = container.attrs.get("State", {})
            running = bool(state.get("Running"))
            started = state.get("StartedAt")
            reached = (
                (action == "stop" and not running)
                or (action == "start" and running)
                or (action == "restart" and running and started != before_started)
            )
            if reached:
                health = state.get("Health", {}).get("Status")
                return {
                    "name": container.name,
                    "state": state.get("Status", "unknown"),
                    "healthy": health == "healthy" if health else running,
                    "health": health or ("running" if running else "none"),
                }
            await asyncio.sleep(0.2)
        raise TimeoutError("Container did not reach the requested state")

    @classmethod
    def get_container_stats(cls, container_id: str) -> dict[str, Any]:
        """Get container resource stats."""
        container = cls.get_container(container_id)
        if container is None:
            return {}
        try:
            return dict(container.stats(stream=False))
        except Exception:
            logger.warning("Failed to get stats for container: %s", container_id)
            return {}

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
            logger.warning("Failed to fetch logs for container: %s", container_id)
            return ""
