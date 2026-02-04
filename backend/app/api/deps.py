"""
API dependencies.
"""

from typing import Annotated

from fastapi import Depends, HTTPException

from app.core.registry import ServiceRegistry
from app.services.base import BaseService
from app.services.minio import MinIOService
from app.services.mongodb import MongoDBService
from app.services.postgres import PostgresService
from app.services.qdrant import QdrantService
from app.services.redis import RedisService


def get_service(service_name: str) -> BaseService:
    """Get a service by name."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )
    return service


def get_postgres_service() -> PostgresService:
    """Get PostgreSQL service."""
    service = ServiceRegistry.get("postgres")
    if service is None or not isinstance(service, PostgresService):
        raise HTTPException(status_code=404, detail="PostgreSQL service not available")
    return service


def get_redis_service() -> RedisService:
    """Get Redis service."""
    service = ServiceRegistry.get("redis")
    if service is None or not isinstance(service, RedisService):
        raise HTTPException(status_code=404, detail="Redis service not available")
    return service


def get_mongodb_service() -> MongoDBService:
    """Get MongoDB service."""
    service = ServiceRegistry.get("mongodb")
    if service is None or not isinstance(service, MongoDBService):
        raise HTTPException(status_code=404, detail="MongoDB service not available")
    return service


def get_qdrant_service() -> QdrantService:
    """Get Qdrant service."""
    service = ServiceRegistry.get("qdrant")
    if service is None or not isinstance(service, QdrantService):
        raise HTTPException(status_code=404, detail="Qdrant service not available")
    return service


def get_minio_service() -> MinIOService:
    """Get MinIO service."""
    service = ServiceRegistry.get("minio")
    if service is None or not isinstance(service, MinIOService):
        raise HTTPException(status_code=404, detail="MinIO service not available")
    return service


# Type aliases for dependency injection
PostgresDep = Annotated[PostgresService, Depends(get_postgres_service)]
RedisDep = Annotated[RedisService, Depends(get_redis_service)]
MongoDBDep = Annotated[MongoDBService, Depends(get_mongodb_service)]
QdrantDep = Annotated[QdrantService, Depends(get_qdrant_service)]
MinIODep = Annotated[MinIOService, Depends(get_minio_service)]
