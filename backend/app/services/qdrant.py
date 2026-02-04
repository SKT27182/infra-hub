"""
Qdrant vector database service implementation.
"""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.services.base import BaseService, ServiceHealth


class QdrantService(BaseService):
    """Qdrant vector database service."""

    name = "qdrant"
    display_name = "Qdrant"
    container_name = "infra-qdrant"
    admin_url = "http://localhost:6333/dashboard"
    admin_container = None  # Qdrant has built-in dashboard

    def _get_client(self) -> QdrantClient:
        """Get Qdrant client."""
        return QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
        )

    async def check_health(self) -> ServiceHealth:
        """Check Qdrant connectivity."""
        try:
            client = self._get_client()
            # Use sync client method (qdrant-client is sync by default)
            collections = client.get_collections()
            client.close()
            return ServiceHealth(
                healthy=True,
                message="Qdrant is responding",
                details={"collections_count": len(collections.collections)},
            )
        except Exception as e:
            return ServiceHealth(
                healthy=False,
                message=f"Qdrant connection failed: {e}",
            )

    async def get_info(self) -> dict[str, Any]:
        """Get Qdrant server information."""
        try:
            client = self._get_client()

            # Get collections
            collections_response = client.get_collections()
            collections = []

            for coll in collections_response.collections:
                try:
                    info = client.get_collection(coll.name)
                    collections.append(
                        {
                            "name": coll.name,
                            "vectors_count": info.vectors_count,
                            "points_count": info.points_count,
                            "status": info.status.value if info.status else "unknown",
                        }
                    )
                except UnexpectedResponse:
                    collections.append(
                        {"name": coll.name, "error": "Failed to get details"}
                    )

            client.close()

            return {
                "collections": collections,
                "total_collections": len(collections),
            }
        except Exception as e:
            return {"error": str(e)}

    async def list_collections(self) -> list[dict[str, Any]]:
        """List all collections with details."""
        try:
            client = self._get_client()
            collections_response = client.get_collections()
            collections = []

            for coll in collections_response.collections:
                try:
                    info = client.get_collection(coll.name)
                    collections.append(
                        {
                            "name": coll.name,
                            "vectors_count": info.vectors_count,
                            "points_count": info.points_count,
                            "indexed_vectors_count": info.indexed_vectors_count,
                            "status": info.status.value if info.status else "unknown",
                            "config": {
                                "vector_size": (
                                    info.config.params.vectors.size  # type: ignore
                                    if hasattr(info.config.params, "vectors")
                                    and hasattr(info.config.params.vectors, "size")
                                    else None
                                ),
                            },
                        }
                    )
                except (UnexpectedResponse, AttributeError) as e:
                    collections.append({"name": coll.name, "error": str(e)})

            client.close()
            return collections
        except Exception as e:
            return [{"error": str(e)}]

    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get detailed collection information."""
        try:
            client = self._get_client()
            info = client.get_collection(collection_name)
            client.close()

            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.value if info.status else "unknown",
                "optimizer_status": str(info.optimizer_status),
                "segments_count": info.segments_count,
            }
        except Exception as e:
            return {"error": str(e)}
