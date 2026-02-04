"""
Redis deep management endpoints.
"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import RedisDep

router = APIRouter(prefix="/redis", tags=["Redis"])


@router.get("/keys")
async def list_keys(
    service: RedisDep,
    pattern: str = "*",
    count: int = 100,
) -> list[dict[str, Any]]:
    """List Redis keys matching pattern."""
    return await service.list_keys(pattern=pattern, count=count)


@router.get("/memory")
async def get_memory_stats(service: RedisDep) -> dict[str, Any]:
    """Get Redis memory statistics."""
    return await service.get_memory_stats()
