"""
Health check endpoints.
"""

from fastapi import APIRouter

from app.core.docker import DockerClient

router = APIRouter()


@router.get("/api/health")
async def health_check() -> dict[str, str]:
    """API health check endpoint."""
    return {"status": "healthy", "service": "infra-hub-api"}


@router.get("/api/health/docker")
async def docker_health() -> dict[str, str | bool]:
    """Docker daemon health check."""
    try:
        client = DockerClient.get_client()
        client.ping()
        return {"status": "healthy", "docker": True}
    except Exception as e:
        return {"status": "unhealthy", "docker": False, "error": str(e)}  # type: ignore
