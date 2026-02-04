"""
Redis service implementation.
"""

from typing import Any

import redis.asyncio as redis

from app.core.config import settings
from app.services.base import BaseService, ServiceHealth


class RedisService(BaseService):
    """Redis cache service."""

    name = "redis"
    display_name = "Redis"
    container_name = "infra-redis"
    admin_url = "http://localhost:5540"
    admin_container = "infra-redisinsight"

    def _get_client(self) -> redis.Redis:  # type: ignore
        """Get Redis client."""
        return redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
        )

    async def check_health(self) -> ServiceHealth:
        """Check Redis connectivity."""
        try:
            client = self._get_client()
            await client.ping()
            info = await client.info("server")
            await client.aclose()
            return ServiceHealth(
                healthy=True,
                message="Redis is responding",
                details={"version": info.get("redis_version")},
            )
        except Exception as e:
            return ServiceHealth(
                healthy=False,
                message=f"Redis connection failed: {e}",
            )

    async def get_info(self) -> dict[str, Any]:
        """Get Redis server information."""
        try:
            client = self._get_client()

            # Get server info
            server_info = await client.info("server")
            memory_info = await client.info("memory")
            stats_info = await client.info("stats")
            keyspace_info = await client.info("keyspace")

            # Get database size
            db_size = await client.dbsize()

            await client.aclose()

            return {
                "version": server_info.get("redis_version"),
                "uptime_seconds": server_info.get("uptime_in_seconds"),
                "connected_clients": stats_info.get("connected_clients", 0),
                "used_memory": memory_info.get("used_memory_human"),
                "peak_memory": memory_info.get("used_memory_peak_human"),
                "total_keys": db_size,
                "keyspace": keyspace_info,
            }
        except Exception as e:
            return {"error": str(e)}

    async def list_keys(
        self, pattern: str = "*", count: int = 100
    ) -> list[dict[str, Any]]:
        """List keys matching pattern."""
        try:
            client = self._get_client()
            keys = []

            async for key in client.scan_iter(match=pattern, count=count):
                if len(keys) >= count:
                    break
                key_type = await client.type(key)
                ttl = await client.ttl(key)
                keys.append(
                    {
                        "key": key,
                        "type": key_type,
                        "ttl": ttl if ttl > 0 else None,
                    }
                )

            await client.aclose()
            return keys
        except Exception as e:
            return [{"error": str(e)}]

    async def get_memory_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        try:
            client = self._get_client()
            memory_info = await client.info("memory")
            await client.aclose()
            return {
                "used_memory": memory_info.get("used_memory"),
                "used_memory_human": memory_info.get("used_memory_human"),
                "used_memory_peak": memory_info.get("used_memory_peak"),
                "used_memory_peak_human": memory_info.get("used_memory_peak_human"),
                "used_memory_rss": memory_info.get("used_memory_rss"),
                "mem_fragmentation_ratio": memory_info.get("mem_fragmentation_ratio"),
            }
        except Exception as e:
            return {"error": str(e)}
