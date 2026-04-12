from fastapi import APIRouter
from infra_docker import DockerClient

router = APIRouter()


@router.get("/health")
async def check_all_health():
    """Check health of all containers starting with 'infra-'."""
    containers = DockerClient.list_containers(all=True)
    infra_containers = [c for c in containers if c.name.startswith("infra-")]

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

    return {
        "status": "healthy" if all(c["healthy"] for c in results) else "unhealthy",
        "containers": results,
    }


@router.get("/containers")
async def list_containers(all: bool = True):
    """List all Docker containers."""
    containers = DockerClient.list_containers(all=all)
    return [
        {
            "id": c.short_id,
            "name": c.name,
            "image": str(c.image.tags[0]) if c.image.tags else "unknown",
            "status": c.status,
            "state": c.attrs.get("State", {}).get("Status", "unknown"),
            "created": c.attrs.get("Created"),
            "ports": list(c.attrs.get("NetworkSettings", {}).get("Ports", {}).keys()),
            "labels": c.labels,
        }
        for c in containers
    ]


@router.get("/containers/infra")
async def list_infra_containers():
    """List only infra containers."""
    containers = await list_containers(all=True)
    return [c for c in containers if c["name"].startswith("infra-")]


@router.post("/containers/{id}/start")
async def start_container(id: str):
    return {"success": DockerClient.start_container(id)}


@router.post("/containers/{id}/stop")
async def stop_container(id: str):
    return {"success": DockerClient.stop_container(id)}


@router.post("/containers/{id}/restart")
async def restart_container(id: str):
    return {"success": DockerClient.restart_container(id)}
