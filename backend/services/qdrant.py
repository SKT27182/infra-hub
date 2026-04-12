"""
Qdrant vector database service implementation.
"""

from typing import Any

from qdrant_client import QdrantClient

from config import settings
from .base import BaseService


class QdrantService(BaseService):
    """Qdrant vector database service."""

    name = "qdrant"
    display_name = "Qdrant"
    container_name = "infra-qdrant"
    admin_url = "http://localhost:6333/dashboard"

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

            return {
                "status": self.get_status().model_dump(),
                "connection": {
                    "url": f"http://127.0.0.1:{settings.qdrant_port}",
                    "host": "127.0.0.1",
                    "port": settings.qdrant_port,
                },
                "collections": details,
                "total_collections": len(details),
            }
        except Exception as e:
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

    async def query(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
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
                    "next_page_offset": str(next_page_offset) if next_page_offset else None,
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
                    return {"success": False, "error": "vector must be a non-empty array"}
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
            return {"success": False, "error": str(e)}
        finally:
            client.close()
