"""
OpenSearch service implementation (full-text, autocomplete, k-NN).
"""

import asyncio
import json
import math
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
            timeout=settings.service_request_timeout_seconds,
        )

    async def get_info(self) -> dict[str, Any]:
        """Get cluster health, indices, and connection details."""
        try:
            client = self._get_client()
            health = await asyncio.to_thread(client.cluster.health)
            indices_raw = await asyncio.to_thread(
                client.cat.indices,
                format="json",
                h="index,docs.count,store.size,health,status",
            )
            indices: list[dict[str, Any]] = []
            visible_rows = [
                row
                for row in (indices_raw or [])
                if not str(row.get("index", "")).startswith(".")
            ]
            for row in visible_rows[:500]:
                name = str(row.get("index", ""))
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
                "indices_truncated": len(visible_rows) > 500,
            }
        except Exception as e:
            logger.warning("OpenSearch get_info failed (%s)", type(e).__name__)
            return {"error": "OpenSearch information is unavailable", "status": self.get_status().model_dump()}

    async def delete_index(self, name: str) -> bool:
        """Delete an index by name."""
        try:
            client = self._get_client()
            if not await asyncio.to_thread(client.indices.exists, index=name):
                client.close()
                return False
            await asyncio.to_thread(client.indices.delete, index=name)
            client.close()
            return True
        except Exception as e:
            logger.error("OpenSearch delete_index failed name=%s type=%s", name, type(e).__name__)
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
                return {
                    "success": True,
                    "result": await asyncio.to_thread(client.cluster.health),
                }

            if action == "list_indices":
                rows = await asyncio.to_thread(
                    client.cat.indices,
                    format="json",
                    h="index,docs.count,store.size,health,status",
                )
                all_indices = [
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
                indices = all_indices[:500]
                return {
                    "success": True,
                    "result": indices,
                    "count": len(indices),
                    "truncated": len(all_indices) > 500,
                }

            index = str(payload.get("index") or "").strip()
            if action in {"index_info", "search", "knn_search", "suggest", "delete_index"} and not index:
                return {"success": False, "error": "index is required"}

            if action == "index_info":
                if not await asyncio.to_thread(client.indices.exists, index=index):
                    return {"success": False, "error": f"Index not found: {index}"}
                stats = await asyncio.to_thread(client.indices.stats, index=index)
                mapping = await asyncio.to_thread(client.indices.get_mapping, index=index)
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
                    if len(json.dumps(body).encode("utf-8")) > 256 * 1024:
                        return {"success": False, "error": "Query DSL body exceeds 256 KiB"}
                    body = {**body, "size": self._clamp_size(body.get("size"))}
                    response = await asyncio.to_thread(client.search, index=index, body=body)
                else:
                    query_text = str(payload.get("query") or "").strip()
                    if not query_text:
                        return {
                            "success": False,
                            "error": "Provide body (Query DSL) or query (match_all / match text)",
                        }
                    field = str(payload.get("field") or "content")
                    response = await asyncio.to_thread(
                        client.search,
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
                    return {"success": False, "error": "vector must contain finite numbers and have at most 65536 dimensions"}
                field = str(payload.get("field") or "embedding")
                k = self._clamp_size(payload.get("k") or payload.get("size"), default=5)
                response = await asyncio.to_thread(
                    client.search,
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
                response = await asyncio.to_thread(
                    client.search,
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
            logger.error("OpenSearch query failed action=%s type=%s", action, type(e).__name__)
            return {"success": False, "error": "OpenSearch request failed"}
        finally:
            client.close()
