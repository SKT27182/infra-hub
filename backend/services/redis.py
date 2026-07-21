"""
Redis service implementation.
"""

from typing import Any

import redis.asyncio as redis

from config import settings
from utils.logger import create_logger

from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)


class RedisService(BaseService):
    """Redis cache service."""

    name = settings.redis_service_name
    display_name = settings.redis_display_name
    container_name = settings.redis_container_name
    admin_url = settings.redis_admin_url
    admin_container = settings.redisinsight_container_name

    def _get_client(self) -> redis.Redis:
        return redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
            socket_connect_timeout=settings.service_request_timeout_seconds,
            socket_timeout=settings.service_request_timeout_seconds,
        )

    async def get_info(self) -> dict[str, Any]:
        """Get Redis information including memory, keys, and clients."""
        client: redis.Redis | None = None
        try:
            client = self._get_client()
            mem = await client.info("memory")
            clients_info = await client.info("clients")
            server_info = await client.info("server")
            db_size = await client.dbsize()
            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.redis_admin_url,
                    instructions=[
                        "Open RedisInsight; the connection 'infra-redis' is preconfigured.",
                        "Host apps use redis:// on the host-mapped port with REDIS_PASSWORD from backend/.env.",
                    ],
                    login={"password_env": "REDIS_PASSWORD"},
                ),
                "connection": {
                    "url": f"redis://{settings.service_public_host}:{settings.redis_port}",
                    "host": settings.service_public_host,
                    "port": settings.redis_port,
                },
                "memory": {
                    "used": mem.get("used_memory_human"),
                    "peak": mem.get("used_memory_peak_human"),
                },
                "total_keys": db_size,
                "connected_clients": clients_info.get("connected_clients", 0),
                "blocked_clients": clients_info.get("blocked_clients", 0),
                "redis_version": server_info.get("redis_version", "unknown"),
                "uptime_seconds": server_info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.warning("Redis get_info failed (%s)", type(e).__name__)
            return {"error": "Redis information is unavailable", "status": self.get_status().model_dump()}
        finally:
            if client is not None:
                await client.aclose()

    async def query(
        self, command: str, args: list[Any] | None = None
    ) -> dict[str, Any]:
        """Execute an arbitrary Redis command."""
        client: redis.Redis | None = None
        try:
            client = self._get_client()
            result = await client.execute_command(command, *(args or []))  # type: ignore[no-untyped-call]
            return {"success": True, "result": result}
        except Exception as e:
            logger.error("Redis command failed command=%s type=%s", command, type(e).__name__)
            return {"success": False, "error": "Redis command failed"}
        finally:
            if client is not None:
                await client.aclose()
