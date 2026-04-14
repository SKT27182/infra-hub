"""
Redis service implementation.
"""

from typing import Any

import redis.asyncio as redis

from config import settings
from .base import BaseService


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
        )

    async def get_info(self) -> dict[str, Any]:
        """Get Redis information including memory, keys, and clients."""
        try:
            client = self._get_client()
            mem = await client.info("memory")
            clients_info = await client.info("clients")
            server_info = await client.info("server")
            db_size = await client.dbsize()
            await client.aclose()

            return {
                "status": self.get_status().model_dump(),
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
            return {"error": str(e), "status": self.get_status().model_dump()}

    async def query(
        self, command: str, args: list[Any] | None = None
    ) -> dict[str, Any]:
        """Execute an arbitrary Redis command."""
        try:
            client = self._get_client()
            result = await client.execute_command(command, *(args or []))
            await client.aclose()

            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
