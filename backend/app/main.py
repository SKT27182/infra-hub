"""
Infra Hub Backend - Centralized Infrastructure Management API
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import containers, health
from app.api.routes import services_api as services
from app.api.routes.services import minio as minio_routes
from app.api.routes.services import mongodb as mongodb_routes
from app.api.routes.services import postgres as postgres_routes
from app.api.routes.services import qdrant as qdrant_routes
from app.api.routes.services import redis as redis_routes
from app.core.config import settings
from app.core.docker import DockerClient
from app.core.registry import ServiceRegistry
from app.services.minio import MinIOService
from app.services.mongodb import MongoDBService
from app.services.postgres import PostgresService
from app.services.qdrant import QdrantService
from app.services.redis import RedisService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize Docker client and register services
    DockerClient.initialize()

    # Register all managed services
    ServiceRegistry.register(PostgresService())
    ServiceRegistry.register(RedisService())
    ServiceRegistry.register(MongoDBService())
    ServiceRegistry.register(QdrantService())
    ServiceRegistry.register(MinIOService())

    yield

    # Shutdown: Cleanup
    DockerClient.close()


app = FastAPI(
    title="Infra Hub API",
    description="Centralized Infrastructure Management Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(containers.router, prefix="/api/containers", tags=["Containers"])
app.include_router(services.router, prefix="/api/services", tags=["Services"])

# Deep service management routes
app.include_router(postgres_routes.router, prefix="/api/services", tags=["PostgreSQL"])
app.include_router(redis_routes.router, prefix="/api/services", tags=["Redis"])
app.include_router(mongodb_routes.router, prefix="/api/services", tags=["MongoDB"])
app.include_router(qdrant_routes.router, prefix="/api/services", tags=["Qdrant"])
app.include_router(minio_routes.router, prefix="/api/services", tags=["MinIO"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Infra Hub API", "docs": "/docs"}
