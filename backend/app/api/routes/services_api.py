"""
Service management endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.registry import ServiceRegistry
from app.schemas.service import (
    AllServicesResponse,
    ServiceActionResponse,
    ServiceHealthResponse,
    ServiceInfoResponse,
    ServiceStatusResponse,
)

router = APIRouter()


@router.get("")
async def list_services() -> AllServicesResponse:
    """List all registered services with their status."""
    services = ServiceRegistry.all()
    statuses = []
    healthy_count = 0

    for service in services:
        status = service.get_status()
        statuses.append(
            ServiceStatusResponse(
                name=status.name,
                display_name=status.display_name,
                running=status.running,
                healthy=status.healthy,
                container_id=status.container_id,
                container_name=status.container_name,
                status=status.status,
                uptime=status.uptime,
                ports=status.ports,
                admin_url=status.admin_url,
            )
        )
        if status.healthy:
            healthy_count += 1

    return AllServicesResponse(
        services=statuses,
        total=len(statuses),
        healthy=healthy_count,
        unhealthy=len(statuses) - healthy_count,
    )


@router.get("/{service_name}")
async def get_service(service_name: str) -> ServiceStatusResponse:
    """Get a specific service status."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    status = service.get_status()
    return ServiceStatusResponse(
        name=status.name,
        display_name=status.display_name,
        running=status.running,
        healthy=status.healthy,
        container_id=status.container_id,
        container_name=status.container_name,
        status=status.status,
        uptime=status.uptime,
        ports=status.ports,
        admin_url=status.admin_url,
    )


@router.get("/{service_name}/health")
async def check_service_health(service_name: str) -> ServiceHealthResponse:
    """Perform a health check on a specific service."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    health = await service.check_health()
    return ServiceHealthResponse(
        healthy=health.healthy,
        message=health.message,
        details=health.details,
    )


@router.get("/{service_name}/info")
async def get_service_info(service_name: str) -> ServiceInfoResponse:
    """Get detailed information about a service."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    info = await service.get_info()
    return ServiceInfoResponse(name=service_name, info=info)


@router.post("/{service_name}/start")
async def start_service(service_name: str) -> ServiceActionResponse:
    """Start a service."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    success = service.start()
    return ServiceActionResponse(
        success=success,
        message=(
            f"Service '{service_name}' started"
            if success
            else f"Failed to start '{service_name}'"
        ),
        service=service_name,
    )


@router.post("/{service_name}/stop")
async def stop_service(service_name: str) -> ServiceActionResponse:
    """Stop a service."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    success = service.stop()
    return ServiceActionResponse(
        success=success,
        message=(
            f"Service '{service_name}' stopped"
            if success
            else f"Failed to stop '{service_name}'"
        ),
        service=service_name,
    )


@router.post("/{service_name}/restart")
async def restart_service(service_name: str) -> ServiceActionResponse:
    """Restart a service."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    success = service.restart()
    return ServiceActionResponse(
        success=success,
        message=(
            f"Service '{service_name}' restarted"
            if success
            else f"Failed to restart '{service_name}'"
        ),
        service=service_name,
    )


@router.get("/{service_name}/logs")
async def get_service_logs(service_name: str, tail: int = 100) -> dict[str, Any]:
    """Get service logs."""
    service = ServiceRegistry.get(service_name)
    if service is None:
        raise HTTPException(
            status_code=404, detail=f"Service '{service_name}' not found"
        )

    logs = service.get_logs(tail=tail)
    return {
        "service": service_name,
        "logs": logs,
        "lines": len(logs.splitlines()),
    }
