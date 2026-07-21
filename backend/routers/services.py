import asyncio
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from config import settings
from services.auth import get_current_user
from services.minio import MinIOService
from services.mongodb import MongoDBService
from services.neo4j import Neo4jService
from services.opensearch import OpenSearchService
from services.postgres import PostgresService
from services.qdrant import QdrantService
from services.redis import RedisService
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)

router = APIRouter(prefix="/services", dependencies=[Depends(get_current_user)])

# Instantiate services
postgres = PostgresService()
redis = RedisService()
minio = MinIOService()
mongodb = MongoDBService()
qdrant = QdrantService()
neo4j = Neo4jService()
opensearch = OpenSearchService()

SERVICES = {
    "postgres": postgres,
    "redis": redis,
    "minio": minio,
    "mongodb": mongodb,
    "qdrant": qdrant,
    "neo4j": neo4j,
    "opensearch": opensearch,
}


class PostgresQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1_000_000)
    database: str | None = Field(default=None, max_length=63)


class RedisQueryRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=64)
    args: list[Any] = Field(default_factory=list)


class GenericActionQueryRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def list_services() -> dict[str, Any]:
    """List all services with their status."""
    status_models = await asyncio.gather(
        *(asyncio.to_thread(service.get_status) for service in SERVICES.values())
    )
    statuses = [model.model_dump() for model in status_models]
    healthy = len([s for s in statuses if s["healthy"]])
    return {
        "services": statuses,
        "total": len(statuses),
        "healthy": healthy,
        "unhealthy": len(statuses) - healthy,
    }


@router.get("/{name}")
async def get_service(name: str) -> dict[str, Any]:
    """Get a specific service status."""
    if name not in SERVICES:
        logger.debug("Service not found: %s", name)
        raise HTTPException(status_code=404, detail="Service not found")
    return (await asyncio.to_thread(SERVICES[name].get_status)).model_dump()


@router.get("/{name}/info")
async def get_service_info(name: str) -> dict[str, Any]:
    """Get detailed information about a service."""
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"name": name, "info": await SERVICES[name].get_info()}


@router.get("/{name}/health")
async def get_service_health(name: str) -> dict[str, Any]:
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    status = await asyncio.to_thread(SERVICES[name].get_status)
    return {
        "healthy": status.healthy,
        "message": "Healthy" if status.healthy else "Unhealthy",
        "details": {"status": status.status, "running": status.running},
    }


@router.get("/{name}/logs")
async def get_service_logs(
    name: str, tail: int = Query(default=100, ge=1, le=1000)
) -> dict[str, Any]:
    if name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    logs = await asyncio.to_thread(SERVICES[name].get_logs, tail=tail)
    return {"service": name, "logs": logs, "lines": len(logs.splitlines())}


@router.post("/{name}/start")
async def start_service(name: str) -> dict[str, Any]:
    if name not in SERVICES:
        logger.debug("Service not found: %s", name)
        raise HTTPException(status_code=404, detail="Service not found")
    return await _service_action(name, "start")


@router.post("/{name}/stop")
async def stop_service(name: str) -> dict[str, Any]:
    if name not in SERVICES:
        logger.debug("Service not found: %s", name)
        raise HTTPException(status_code=404, detail="Service not found")
    return await _service_action(name, "stop")


@router.post("/{name}/restart")
async def restart_service(name: str) -> dict[str, Any]:
    if name not in SERVICES:
        logger.debug("Service not found: %s", name)
        raise HTTPException(status_code=404, detail="Service not found")
    return await _service_action(name, "restart")


async def _service_action(
    name: str, action: Literal["start", "stop", "restart"]
) -> dict[str, Any]:
    try:
        containers = await SERVICES[name].action(action)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    logger.info("Service %s completed for %s", action, name)
    return {
        "success": True,
        "action": action,
        "service": name,
        "containers": containers,
        "message": f"Service {action} completed",
    }


# Service-specific actions
@router.post("/postgres/databases/{db_name}")
async def create_pg_db(db_name: str) -> dict[str, bool]:
    return {"success": await postgres.create_database(db_name)}


@router.delete("/postgres/databases/{db_name}")
async def drop_pg_db(db_name: str) -> dict[str, bool]:
    return {"success": await postgres.drop_database(db_name)}


@router.post("/postgres/query")
async def query_postgres(payload: PostgresQueryRequest) -> dict[str, Any]:
    logger.verbose("Postgres query on database=%s", payload.database)
    return _result_or_error(await postgres.query(payload.query, payload.database))


@router.post("/redis/query")
async def query_redis(payload: RedisQueryRequest) -> dict[str, Any]:
    return _result_or_error(await redis.query(payload.command, payload.args))


@router.post("/mongodb/query")
async def query_mongodb(payload: GenericActionQueryRequest) -> dict[str, Any]:
    return _result_or_error(await mongodb.query(payload.action, payload.params))


@router.post("/minio/query")
async def query_minio(payload: GenericActionQueryRequest) -> dict[str, Any]:
    return _result_or_error(await minio.query(payload.action, payload.params))


@router.post("/qdrant/query")
async def query_qdrant(payload: GenericActionQueryRequest) -> dict[str, Any]:
    return _result_or_error(await qdrant.query(payload.action, payload.params))


@router.post("/neo4j/query")
async def query_neo4j(payload: GenericActionQueryRequest) -> dict[str, Any]:
    return _result_or_error(await neo4j.query(payload.action, payload.params))


@router.post("/opensearch/query")
async def query_opensearch(payload: GenericActionQueryRequest) -> dict[str, Any]:
    return _result_or_error(await opensearch.query(payload.action, payload.params))


def _result_or_error(result: dict[str, Any]) -> dict[str, Any]:
    """Convert legacy internal result flags to proper v2 HTTP failures."""
    if result.get("success") is not False:
        return result
    message = str(result.get("error") or "Service operation failed")
    lowered = message.lower()
    if "timed out" in lowered:
        status_code = 504
    elif any(token in lowered for token in ("required", "must", "only one", "single", "unsupported", "unknown action", "cannot be empty", "exceeds")):
        status_code = 422
    else:
        status_code = 502
    raise HTTPException(status_code=status_code, detail=message)


@router.post("/minio/buckets/{bucket_name}")
async def create_minio_bucket(bucket_name: str) -> dict[str, bool]:
    return {"success": await minio.create_bucket(bucket_name)}


@router.delete("/minio/buckets/{bucket_name}")
async def drop_minio_bucket(bucket_name: str) -> dict[str, bool]:
    return {"success": await minio.drop_bucket(bucket_name)}


@router.delete("/mongodb/databases/{db_name}")
async def drop_mongodb_db(db_name: str) -> dict[str, bool]:
    return {"success": await mongodb.drop_database(db_name)}


@router.delete("/qdrant/collections/{name}")
async def delete_qdrant_coll(name: str) -> dict[str, bool]:
    return {"success": await qdrant.delete_collection(name)}


@router.delete("/opensearch/indices/{name}")
async def delete_opensearch_index(name: str) -> dict[str, bool]:
    return {"success": await opensearch.delete_index(name)}
