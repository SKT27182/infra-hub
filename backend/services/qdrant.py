"""
Qdrant vector database service implementation.
"""

import asyncio
import math
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
            timeout=int(settings.service_request_timeout_seconds),
        )

    async def get_info(self) -> dict[str, Any]:
        """Get minimal but complete Qdrant information."""
        try:
            client = self._get_client()
            response = await asyncio.to_thread(client.get_collections)
            details = []
            for coll in response.collections[:500]:
                try:
                    info = await asyncio.to_thread(client.get_collection, coll.name)
                    details.append(
                        {
                            "name": coll.name,
                            "indexed_vectors": info.indexed_vectors_count,
                            "points": info.points_count,
                        }
                    )
                except (RuntimeError, ValueError, TypeError):
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
                "collections_truncated": len(response.collections) > 500,
            }
        except Exception as e:
            logger.warning("Qdrant get_info failed (%s)", type(e).__name__)
            return {"error": "Qdrant information is unavailable", "status": self.get_status().model_dump()}

    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            client = self._get_client()
            await asyncio.to_thread(client.delete_collection, name)
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
                response = await asyncio.to_thread(client.get_collections)
                return {
                    "success": True,
                    "result": [collection.name for collection in response.collections[:500]],
                    "truncated": len(response.collections) > 500,
                }

            collection = str(payload.get("collection") or "").strip()
            if not collection:
                return {"success": False, "error": "collection is required"}

            if action == "collection_info":
                info = await asyncio.to_thread(client.get_collection, collection)
                return {
                    "success": True,
                    "result": {
                        "name": collection,
                        "status": info.status.value if info.status else None,
                        "points_count": info.points_count,
                        "indexed_vectors_count": info.indexed_vectors_count,
                    },
                }

            if action == "scroll":
                limit = max(1, min(int(payload.get("limit", 10)), 100))
                with_payload = bool(payload.get("with_payload", True))
                with_vectors = bool(payload.get("with_vectors", False))
                points, next_page_offset = await asyncio.to_thread(
                    client.scroll,
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
                if (
                    not isinstance(vector, list)
                    or not vector
                    or len(vector) > 65_536
                    or any(
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        for value in vector
                    )
                ):
                    return {
                        "success": False,
                        "error": "vector must contain finite numbers and have at most 65536 dimensions",
                    }
                limit = max(1, min(int(payload.get("limit", 5)), 100))
                with_payload = bool(payload.get("with_payload", True))
                query_response: Any = await asyncio.to_thread(
                    lambda: client.query_points(
                        collection_name=collection,
                        query=vector,
                        limit=limit,
                        with_payload=with_payload,
                    )
                )
                results = query_response.points
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
            logger.error("Qdrant query failed action=%s type=%s", action, type(e).__name__)
            return {"success": False, "error": "Qdrant request failed"}
        finally:
            client.close()
