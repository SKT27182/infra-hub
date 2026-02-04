"""
MinIO deep management endpoints.
"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import MinIODep

router = APIRouter(prefix="/minio", tags=["MinIO"])


@router.get("/buckets")
async def list_buckets(service: MinIODep) -> list[dict[str, Any]]:
    """List all MinIO buckets."""
    return await service.list_buckets()


@router.get("/buckets/{bucket_name}")
async def get_bucket(bucket_name: str, service: MinIODep) -> dict[str, Any]:
    """Get bucket details including objects."""
    return await service.get_bucket_info(bucket_name)
