"""
PostgreSQL deep management endpoints.
"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import PostgresDep

router = APIRouter(prefix="/postgres", tags=["PostgreSQL"])


@router.get("/databases")
async def list_databases(service: PostgresDep) -> list[dict[str, Any]]:
    """List all PostgreSQL databases."""
    return await service.list_databases()


@router.get("/databases/{database}/tables")
async def list_tables(database: str, service: PostgresDep) -> list[dict[str, Any]]:
    """List tables in a database."""
    return await service.list_tables(database)
