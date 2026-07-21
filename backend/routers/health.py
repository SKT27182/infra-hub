import asyncio
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from infra_docker import DockerClient
from services.auth import get_current_user
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/health")
async def check_all_health() -> dict[str, Any]:
    """Check health of all registered Infra Hub containers."""
    containers = await asyncio.to_thread(DockerClient.list_containers, all=True)
    infra_containers = containers

    results = []
    for container in infra_containers:
        status = container.status
        health = container.attrs.get("State", {}).get("Health", {})
        healthy = health.get("Status") == "healthy" if health else (status == "running")

        results.append(
            {
                "name": container.name,
                "status": status,
                "healthy": healthy,
                "id": container.short_id,
            }
        )

    overall = "healthy" if all(c["healthy"] for c in results) else "unhealthy"
    logger.verbose(
        "Health check: %s (%d containers)",
        overall,
        len(results),
    )
    return {
        "status": overall,
        "containers": results,
    }


@router.get("/containers")
async def list_containers(all: bool = True) -> list[dict[str, Any]]:
    """List all Docker containers."""
    containers = await asyncio.to_thread(DockerClient.list_containers, all=all)
    return [
        {
            "id": c.short_id,
            "name": c.name,
            "image": str(c.image.tags[0]) if c.image.tags else "unknown",
            "status": c.status,
            "state": c.attrs.get("State", {}).get("Status", "unknown"),
            "created": c.attrs.get("Created"),
            "ports": list(c.attrs.get("NetworkSettings", {}).get("Ports", {}).keys()),
            "labels": {
                key: value
                for key, value in c.labels.items()
                if key in {"com.docker.compose.project", "com.docker.compose.service"}
            },
        }
        for c in containers
    ]


@router.get("/containers/infra")
async def list_infra_containers() -> list[dict[str, Any]]:
    """List only infra containers."""
    containers = await list_containers(all=True)
    return containers


@router.post("/containers/{id}/start")
async def start_container(id: str) -> dict[str, Any]:
    return await _container_action(id, "start")


@router.post("/containers/{id}/stop")
async def stop_container(id: str) -> dict[str, Any]:
    return await _container_action(id, "stop")


@router.post("/containers/{id}/restart")
async def restart_container(id: str) -> dict[str, Any]:
    return await _container_action(id, "restart")


async def _container_action(
    container_id: str, action: Literal["start", "stop", "restart"]
) -> dict[str, Any]:
    try:
        result = await DockerClient.perform_action(container_id, action)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "success": True,
        "action": action,
        "service": DockerClient.service_name_for_container(result["name"]),
        "containers": [result],
        "message": f"Container {action} completed",
    }
