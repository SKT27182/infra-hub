"""
Container management endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.core.docker import DockerClient
from app.schemas.container import ContainerAction, ContainerInfo, ContainerLogs

router = APIRouter()


def _parse_container(container) -> ContainerInfo:  # type: ignore
    """Parse Docker container to ContainerInfo schema."""
    # Get ports
    ports = []
    port_bindings = container.attrs.get("NetworkSettings", {}).get("Ports", {})
    for container_port, bindings in port_bindings.items():
        if bindings:
            for binding in bindings:
                host_port = binding.get("HostPort", "")
                if host_port:
                    ports.append(f"{host_port}:{container_port}")

    return ContainerInfo(
        id=container.short_id,
        name=container.name,
        image=(
            container.image.tags[0]
            if container.image.tags
            else str(container.image.id)[:12]
        ),
        status=container.status,
        state=container.attrs.get("State", {}).get("Status", "unknown"),
        created=container.attrs.get("Created"),
        ports=ports,
        labels=container.labels or {},
    )


@router.get("")
async def list_containers(all: bool = True) -> list[ContainerInfo]:
    """List all Docker containers."""
    containers = DockerClient.list_containers(all=all)
    return [_parse_container(c) for c in containers]


@router.get("/infra")
async def list_infra_containers() -> list[ContainerInfo]:
    """List only infra-hub managed containers."""
    containers = DockerClient.list_containers(all=True)
    infra_containers = [c for c in containers if c.name.startswith("infra-")]
    return [_parse_container(c) for c in infra_containers]


@router.get("/{container_id}")
async def get_container(container_id: str) -> ContainerInfo:
    """Get container details by ID or name."""
    container = DockerClient.get_container(container_id)
    if container is None:
        raise HTTPException(
            status_code=404, detail=f"Container '{container_id}' not found"
        )
    return _parse_container(container)


@router.post("/{container_id}/start")
async def start_container(container_id: str) -> ContainerAction:
    """Start a container."""
    success = DockerClient.start_container(container_id)
    if not success:
        raise HTTPException(
            status_code=400, detail=f"Failed to start container '{container_id}'"
        )
    return ContainerAction(
        success=True,
        message=f"Container '{container_id}' started successfully",
        container_id=container_id,
    )


@router.post("/{container_id}/stop")
async def stop_container(container_id: str) -> ContainerAction:
    """Stop a container."""
    success = DockerClient.stop_container(container_id)
    if not success:
        raise HTTPException(
            status_code=400, detail=f"Failed to stop container '{container_id}'"
        )
    return ContainerAction(
        success=True,
        message=f"Container '{container_id}' stopped successfully",
        container_id=container_id,
    )


@router.post("/{container_id}/restart")
async def restart_container(container_id: str) -> ContainerAction:
    """Restart a container."""
    success = DockerClient.restart_container(container_id)
    if not success:
        raise HTTPException(
            status_code=400, detail=f"Failed to restart container '{container_id}'"
        )
    return ContainerAction(
        success=True,
        message=f"Container '{container_id}' restarted successfully",
        container_id=container_id,
    )


@router.get("/{container_id}/logs")
async def get_container_logs(container_id: str, tail: int = 100) -> ContainerLogs:
    """Get container logs."""
    container = DockerClient.get_container(container_id)
    if container is None:
        raise HTTPException(
            status_code=404, detail=f"Container '{container_id}' not found"
        )

    logs = DockerClient.get_container_logs(container_id, tail=tail)
    return ContainerLogs(
        container_id=container_id,
        logs=logs,
        lines=len(logs.splitlines()),
    )
