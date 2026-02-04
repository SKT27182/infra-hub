"""
MongoDB deep management endpoints.
"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import MongoDBDep

router = APIRouter(prefix="/mongodb", tags=["MongoDB"])


@router.get("/databases")
async def list_databases(service: MongoDBDep) -> list[dict[str, Any]]:
    """List all MongoDB databases."""
    return await service.list_databases()


@router.get("/databases/{database}/collections")
async def list_collections(database: str, service: MongoDBDep) -> list[dict[str, Any]]:
    """List collections in a database."""
    return await service.list_collections(database)
