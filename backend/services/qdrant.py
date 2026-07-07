"""
Qdrant vector database service implementation.
"""

from typing import Any

from qdrant_client import QdrantClient

from config import settings
from utils.logger import create_logger
from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)


class QdrantService(BaseService):
    """Qdrant vector database service."""

    name = settings.qdrant_service_name
    display_name = settings.qdrant_display_name
    container_name = settings.qdrant_container_name
    admin_url = settings.qdrant_admin_url

    def _get_client(self) -> QdrantClient:
        return QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            https=False,
        )

    async def get_info(self) -> dict[str, Any]:
        """Get minimal but complete Qdrant information."""
        try:
            client = self._get_client()
            response = client.get_collections()
            details = []
            for coll in response.collections:
                try:
                    info = client.get_collection(coll.name)
                    details.append(
                        {
                            "name": coll.name,
                            "vectors": info.vectors_count,
                            "points": info.points_count,
                        }
                    )
                except:
                    details.append(
                        {"name": coll.name, "error": "Could not get details"}
                    )
            client.close()

            api_key_set = bool(settings.qdrant_api_key)
            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.qdrant_admin_url,
                    instructions=[
                        "Open the Qdrant dashboard.",
                        "When prompted for an API key, use the value of QDRANT_API_KEY in backend/.env.",
                        "Apps must pass the same key in the api-key header or QdrantClient api_key.",
                    ],
                    api_key_required=api_key_set,
                    login={"api_key_env": "QDRANT_API_KEY"} if api_key_set else None,
                ),
                "connection": {
                    "url": f"http://{settings.service_public_host}:{settings.qdrant_port}",
                    "host": settings.service_public_host,
                    "port": settings.qdrant_port,
                },
                "collections": details,
                "total_collections": len(details),
            }
        except Exception as e:
            logger.warning("Qdrant get_info failed: %s", e)
            return {"error": str(e), "status": self.get_status().model_dump()}

    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            client = self._get_client()
            client.delete_collection(name)
            client.close()
            return True
        except Exception:
            return False

    async def query(
        self, action: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute Qdrant query actions."""
        payload = params or {}
        client = self._get_client()

        try:
            if action == "list_collections":
                response = client.get_collections()
                return {
                    "success": True,
                    "result": [collection.name for collection in response.collections],
                }

            collection = str(payload.get("collection") or "").strip()
            if not collection:
                return {"success": False, "error": "collection is required"}

            if action == "collection_info":
                info = client.get_collection(collection)
                return {
                    "success": True,
                    "result": {
                        "name": collection,
                        "status": info.status.value if info.status else None,
                        "points_count": info.points_count,
                        "vectors_count": info.vectors_count,
                    },
                }

            if action == "scroll":
                limit = int(payload.get("limit", 10))
                with_payload = bool(payload.get("with_payload", True))
                with_vectors = bool(payload.get("with_vectors", False))
                points, next_page_offset = client.scroll(
                    collection_name=collection,
                    limit=limit,
                    with_payload=with_payload,
                    with_vectors=with_vectors,
                )
                return {
                    "success": True,
                    "count": len(points),
                    "next_page_offset": (
                        str(next_page_offset) if next_page_offset else None
                    ),
                    "result": [
                        {
                            "id": str(point.id),
                            "payload": point.payload,
                            "vector": point.vector if with_vectors else None,
                        }
                        for point in points
                    ],
                }

            if action == "search":
                vector = payload.get("vector")
                if not isinstance(vector, list) or not vector:
                    return {
                        "success": False,
                        "error": "vector must be a non-empty array",
                    }
                limit = int(payload.get("limit", 5))
                with_payload = bool(payload.get("with_payload", True))
                results = client.search(
                    collection_name=collection,
                    query_vector=vector,
                    limit=limit,
                    with_payload=with_payload,
                )
                return {
                    "success": True,
                    "count": len(results),
                    "result": [
                        {
                            "id": str(point.id),
                            "score": point.score,
                            "payload": point.payload if with_payload else None,
                        }
                        for point in results
                    ],
                }

            return {"success": False, "error": f"Unsupported action: {action}"}
        except Exception as e:
            logger.error("Qdrant query failed action=%s: %s", action, e)
            return {"success": False, "error": str(e)}
        finally:
            client.close()
