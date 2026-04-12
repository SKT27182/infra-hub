from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from services.postgres import PostgresService
from services.redis import RedisService
from services.minio import MinIOService
from services.mongodb import MongoDBService
from services.qdrant import QdrantService
from services.auth import get_current_user

router = APIRouter(prefix="/services", dependencies=[Depends(get_current_user)])

# Instantiate services
postgres = PostgresService()
redis = RedisService()
minio = MinIOService()
mongodb = MongoDBService()
qdrant = QdrantService()

SERVICES = {
    "postgres": postgres,
    "redis": redis,
    "minio": minio,
    "mongodb": mongodb,
    "qdrant": qdrant,
}


class PostgresQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    database: str | None = None


class RedisQueryRequest(BaseModel):
    command: str = Field(..., min_length=1)
    args: list[Any] = Field(default_factory=list)


class GenericActionQueryRequest(BaseModel):
    action: str = Field(..., min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def list_services():
    """List all services with their status."""
    statuses = [s.get_status().model_dump() for s in SERVICES.values()]
    healthy = len([s for s in statuses if s["healthy"]])
    return {
        "services": statuses,
        "total": len(statuses),
        "healthy": healthy,
        "unhealthy": len(statuses) - healthy,
    }


@router.get("/{name}")
async def get_service(name: str):
    """Get a specific service status."""
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return SERVICES[name].get_status().model_dump()


@router.get("/{name}/info")
async def get_service_info(name: str):
    """Get detailed information about a service."""
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"name": name, "info": await SERVICES[name].get_info()}


@router.get("/{name}/health")
async def get_service_health(name: str):
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    status = SERVICES[name].get_status()
    return {
        "healthy": status.healthy,
        "message": "Healthy" if status.healthy else "Unhealthy",
        "details": {"status": status.status, "running": status.running},
    }


@router.get("/{name}/logs")
async def get_service_logs(name: str, tail: int = 100):
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    logs = SERVICES[name].get_logs(tail=tail)
    return {"service": name, "logs": logs, "lines": len(logs.splitlines())}


@router.post("/{name}/start")
async def start_service(name: str):
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": SERVICES[name].start()}


@router.post("/{name}/stop")
async def stop_service(name: str):
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": SERVICES[name].stop()}


@router.post("/{name}/restart")
async def restart_service(name: str):
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": SERVICES[name].restart()}


# Service-specific actions
@router.post("/postgres/databases/{db_name}")
async def create_pg_db(db_name: str):
    return {"success": await postgres.create_database(db_name)}


@router.delete("/postgres/databases/{db_name}")
async def drop_pg_db(db_name: str):
    return {"success": await postgres.drop_database(db_name)}


@router.post("/postgres/query")
async def query_postgres(payload: PostgresQueryRequest):
    return await postgres.query(payload.query, payload.database)


@router.post("/redis/query")
async def query_redis(payload: RedisQueryRequest):
    return await redis.query(payload.command, payload.args)


@router.post("/mongodb/query")
async def query_mongodb(payload: GenericActionQueryRequest):
    return await mongodb.query(payload.action, payload.params)


@router.post("/minio/query")
async def query_minio(payload: GenericActionQueryRequest):
    return await minio.query(payload.action, payload.params)


@router.post("/qdrant/query")
async def query_qdrant(payload: GenericActionQueryRequest):
    return await qdrant.query(payload.action, payload.params)


@router.post("/minio/buckets/{bucket_name}")
async def create_minio_bucket(bucket_name: str):
    return {"success": await minio.create_bucket(bucket_name)}


@router.delete("/minio/buckets/{bucket_name}")
async def drop_minio_bucket(bucket_name: str):
    return {"success": await minio.drop_bucket(bucket_name)}


@router.delete("/mongodb/databases/{db_name}")
async def drop_mongodb_db(db_name: str):
    return {"success": await mongodb.drop_database(db_name)}


@router.delete("/qdrant/collections/{name}")
async def delete_qdrant_coll(name: str):
    return {"success": await qdrant.delete_collection(name)}
