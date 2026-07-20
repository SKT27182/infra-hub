"""
OpenSearch service implementation (full-text, autocomplete, k-NN).
"""

from typing import Any

from opensearchpy import OpenSearch, RequestsHttpConnection

from config import settings
from utils.logger import create_logger
from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)

_DEFAULT_SEARCH_SIZE = 10
_MAX_SEARCH_SIZE = 100


class OpenSearchService(BaseService):
    """OpenSearch full-text / vector retrieval service."""

    name = settings.opensearch_service_name
    display_name = settings.opensearch_display_name
    container_name = settings.opensearch_container_name
    admin_url = settings.opensearch_admin_url
    admin_container = settings.opensearch_dashboards_container_name

    def _get_client(self) -> OpenSearch:
        return OpenSearch(
            hosts=[
                {
                    "host": settings.opensearch_host,
                    "port": settings.opensearch_http_port,
                }
            ],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection,
            timeout=30,
        )

    async def get_info(self) -> dict[str, Any]:
        """Get cluster health, indices, and connection details."""
        try:
            client = self._get_client()
            health = client.cluster.health()
            indices_raw = client.cat.indices(format="json", h="index,docs.count,store.size,health,status")
            indices: list[dict[str, Any]] = []
            for row in indices_raw or []:
                name = str(row.get("index", ""))
                if name.startswith("."):
                    continue
                indices.append(
                    {
                        "name": name,
                        "docs_count": int(row.get("docs.count") or 0),
                        "store_size": row.get("store.size"),
                        "health": row.get("health"),
                        "status": row.get("status"),
                    }
                )
            client.close()

            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.opensearch_admin_url,
                    instructions=[
                        "Open OpenSearch Dashboards to explore indices and run Dev Tools queries.",
                        "Local stack runs with the security plugin disabled (no login).",
                        "Apps connect to the HTTP endpoint for BM25, autocomplete, and k-NN search.",
                        "Qdrant remains available for dedicated vector workloads; choose per app.",
                    ],
                ),
                "connection": {
                    "url": settings.opensearch_url,
                    "host": settings.service_public_host,
                    "port": settings.opensearch_http_port,
                    "dashboards_url": settings.opensearch_admin_url,
                },
                "cluster": {
                    "name": health.get("cluster_name"),
                    "status": health.get("status"),
                    "number_of_nodes": health.get("number_of_nodes"),
                    "active_shards": health.get("active_shards"),
                },
                "indices": indices,
                "total_indices": len(indices),
            }
        except Exception as e:
            logger.warning("OpenSearch get_info failed: %s", e)
            return {"error": str(e), "status": self.get_status().model_dump()}

    async def delete_index(self, name: str) -> bool:
        """Delete an index by name."""
        try:
            client = self._get_client()
            if not client.indices.exists(index=name):
                client.close()
                return False
            client.indices.delete(index=name)
            client.close()
            return True
        except Exception as e:
            logger.error("OpenSearch delete_index failed name=%s: %s", name, e)
            return False

    def _clamp_size(self, value: Any, default: int = _DEFAULT_SEARCH_SIZE) -> int:
        try:
            size = int(value) if value is not None else default
        except (TypeError, ValueError):
            size = default
        return max(1, min(size, _MAX_SEARCH_SIZE))

    async def query(
        self, action: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute OpenSearch query actions."""
        payload = params or {}
        client = self._get_client()

        try:
            if action == "cluster_health":
                return {"success": True, "result": client.cluster.health()}

            if action == "list_indices":
                rows = client.cat.indices(format="json", h="index,docs.count,store.size,health,status")
                indices = [
                    {
                        "name": row.get("index"),
                        "docs_count": int(row.get("docs.count") or 0),
                        "store_size": row.get("store.size"),
                        "health": row.get("health"),
                        "status": row.get("status"),
                    }
                    for row in (rows or [])
                    if not str(row.get("index", "")).startswith(".")
                ]
                return {"success": True, "result": indices, "count": len(indices)}

            index = str(payload.get("index") or "").strip()
            if action in {"index_info", "search", "knn_search", "suggest", "delete_index"} and not index:
                return {"success": False, "error": "index is required"}

            if action == "index_info":
                if not client.indices.exists(index=index):
                    return {"success": False, "error": f"Index not found: {index}"}
                stats = client.indices.stats(index=index)
                mapping = client.indices.get_mapping(index=index)
                return {
                    "success": True,
                    "result": {
                        "name": index,
                        "stats": stats.get("indices", {}).get(index, {}),
                        "mappings": mapping.get(index, {}).get("mappings", {}),
                    },
                }

            if action == "search":
                size = self._clamp_size(payload.get("size"))
                body = payload.get("body")
                if isinstance(body, dict):
                    response = client.search(index=index, body=body)
                else:
                    query_text = str(payload.get("query") or "").strip()
                    if not query_text:
                        return {
                            "success": False,
                            "error": "Provide body (Query DSL) or query (match_all / match text)",
                        }
                    field = str(payload.get("field") or "content")
                    response = client.search(
                        index=index,
                        body={
                            "size": size,
                            "query": {
                                "match": {field: query_text},
                            },
                        },
                    )
                hits = response.get("hits", {})
                return {
                    "success": True,
                    "total": hits.get("total"),
                    "count": len(hits.get("hits", [])),
                    "result": hits.get("hits", []),
                    "suggest": response.get("suggest"),
                }

            if action == "knn_search":
                vector = payload.get("vector")
                if not isinstance(vector, list) or not vector:
                    return {"success": False, "error": "vector must be a non-empty array"}
                field = str(payload.get("field") or "embedding")
                k = self._clamp_size(payload.get("k") or payload.get("size"), default=5)
                response = client.search(
                    index=index,
                    body={
                        "size": k,
                        "query": {
                            "knn": {
                                field: {
                                    "vector": vector,
                                    "k": k,
                                }
                            }
                        },
                    },
                )
                hits = response.get("hits", {})
                return {
                    "success": True,
                    "total": hits.get("total"),
                    "count": len(hits.get("hits", [])),
                    "result": hits.get("hits", []),
                }

            if action == "suggest":
                text = str(payload.get("text") or "").strip()
                field = str(payload.get("field") or "suggest")
                size = self._clamp_size(payload.get("size"), default=5)
                if not text:
                    return {"success": False, "error": "text is required for suggest"}
                response = client.search(
                    index=index,
                    body={
                        "suggest": {
                            "completion_suggest": {
                                "prefix": text,
                                "completion": {
                                    "field": field,
                                    "size": size,
                                    "skip_duplicates": True,
                                },
                            }
                        }
                    },
                )
                return {
                    "success": True,
                    "result": response.get("suggest", {}),
                }

            if action == "delete_index":
                deleted = await self.delete_index(index)
                return {"success": deleted, "result": {"deleted": deleted, "index": index}}

            return {"success": False, "error": f"Unsupported action: {action}"}
        except Exception as e:
            logger.error("OpenSearch query failed action=%s: %s", action, e)
            return {"success": False, "error": str(e)}
        finally:
            client.close()
