"""
Qdrant deep management endpoints.
"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import QdrantDep

router = APIRouter(prefix="/qdrant", tags=["Qdrant"])


@router.get("/collections")
async def list_collections(service: QdrantDep) -> list[dict[str, Any]]:
    """List all Qdrant collections."""
    return await service.list_collections()


@router.get("/collections/{collection_name}")
async def get_collection(collection_name: str, service: QdrantDep) -> dict[str, Any]:
    """Get collection details."""
    return await service.get_collection_info(collection_name)
