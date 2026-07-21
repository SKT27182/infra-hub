"""
Neo4j graph database service implementation.
"""

import asyncio
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from config import settings
from utils.logger import create_logger

from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)

_DEFAULT_ROW_LIMIT = 100
_MAX_ROW_LIMIT = 500
_QUERY_TIMEOUT_SECONDS = 10.0


class Neo4jService(BaseService):
    """Neo4j graph database service."""

    name = settings.neo4j_service_name
    display_name = settings.neo4j_display_name
    container_name = settings.neo4j_container_name
    admin_url = settings.neo4j_admin_url

    def _bolt_uri(self) -> str:
        return f"bolt://{settings.neo4j_host}:{settings.neo4j_bolt_port}"

    def _driver(self) -> AsyncDriver:
        return AsyncGraphDatabase.driver(
            self._bolt_uri(),
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=settings.service_request_timeout_seconds,
        )

    async def _close_driver(self, driver: AsyncDriver) -> None:
        await driver.close()

    async def get_info(self) -> dict[str, Any]:
        """Get Neo4j graph statistics and connection details."""
        driver = self._driver()
        try:
            labels: list[str] = []
            relationship_types: list[str] = []
            node_count = 0
            relationship_count = 0

            async with driver.session() as session:
                label_rows = await session.run(
                    "CALL db.labels() YIELD label RETURN label LIMIT 500"
                )
                labels = [str(record["label"]) async for record in label_rows]
                rel_rows = await session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType LIMIT 500"
                )
                relationship_types = [
                    str(record["relationshipType"]) async for record in rel_rows
                ]
                node_row = await session.run("MATCH (n) RETURN count(n) AS count")
                node_record = await node_row.single()
                node_count = int(node_record["count"]) if node_record else 0
                rel_count_row = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
                rel_record = await rel_count_row.single()
                relationship_count = int(rel_record["count"]) if rel_record else 0

            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.neo4j_admin_url,
                    instructions=[
                        "Open Neo4j Browser for interactive graph visualization.",
                        "Sign in with NEO4J_USER and NEO4J_PASSWORD from backend/.env.",
                        "Use the Bolt URI for app connections (FlexSearch Graph RAG, etc.).",
                    ],
                    login={
                        "username_env": "NEO4J_USER",
                        "password_env": "NEO4J_PASSWORD",
                    },
                ),
                "connection": {
                    "url": settings.neo4j_admin_url,
                    "http_url": settings.neo4j_admin_url,
                    "bolt_uri": settings.neo4j_bolt_uri,
                    "user": settings.neo4j_user,
                },
                "labels": labels,
                "relationship_types": relationship_types,
                "node_count": node_count,
                "relationship_count": relationship_count,
            }
        except Exception as e:
            logger.warning("Neo4j get_info failed (%s)", type(e).__name__)
            return {"error": "Neo4j information is unavailable", "status": self.get_status().model_dump()}
        finally:
            await self._close_driver(driver)

    async def _run_cypher(
        self,
        cypher: str,
        params: dict[str, Any],
        limit: int,
    ) -> dict[str, Any]:
        query = cypher.strip()
        if not query:
            return {"success": False, "error": "Query cannot be empty"}
        if ";" in query.rstrip(";"):
            return {"success": False, "error": "Only one statement is allowed"}

        row_limit = min(max(limit, 1), _MAX_ROW_LIMIT)
        driver = self._driver()

        async def _fetch(tx: Any) -> tuple[list[str], list[dict[str, Any]]]:
            result = await tx.run(cypher, params)
            columns = result.keys()
            rows: list[dict[str, Any]] = []
            async for record in result:
                rows.append(record.data())
                if len(rows) > row_limit:
                    break
            return list(columns), rows

        try:
            async with driver.session() as session:
                columns, rows = await asyncio.wait_for(
                    session.execute_write(_fetch),
                    timeout=_QUERY_TIMEOUT_SECONDS,
                )
            return {
                "success": True,
                "columns": columns,
                "result": rows[:row_limit],
                "count": min(len(rows), row_limit),
                "truncated": len(rows) > row_limit,
            }
        except TimeoutError:
            return {"success": False, "error": "Query timed out"}
        except Exception as e:
            logger.error("Neo4j query failed type=%s", type(e).__name__)
            return {"success": False, "error": "Neo4j query failed"}
        finally:
            await self._close_driver(driver)

    async def query(
        self, action: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute Neo4j query actions."""
        payload = params or {}
        driver: AsyncDriver | None = self._driver()

        try:
            assert driver is not None
            if action == "list_labels":
                async with driver.session() as session:
                    result = await session.run("CALL db.labels()")
                    labels = [str(record["label"]) async for record in result]
                return {"success": True, "result": labels, "count": len(labels)}

            if action == "list_relationship_types":
                async with driver.session() as session:
                    result = await session.run("CALL db.relationshipTypes()")
                    types = [str(record["relationshipType"]) async for record in result]
                return {"success": True, "result": types, "count": len(types)}

            if action == "node_counts":
                async with driver.session() as session:
                    result = await session.run(
                        """
                        MATCH (n)
                        UNWIND labels(n) AS label
                        RETURN label, count(*) AS count
                        ORDER BY count DESC
                        LIMIT 500
                        """
                    )
                    rows = [record.data() async for record in result]
                return {"success": True, "result": rows, "count": len(rows)}

            if action == "run_cypher":
                cypher = str(payload.get("cypher") or "").strip()
                limit = int(payload.get("limit") or _DEFAULT_ROW_LIMIT)
                query_params = payload.get("params") or {}
                if not isinstance(query_params, dict):
                    return {"success": False, "error": "params must be an object"}
                await self._close_driver(driver)
                driver = None
                return await self._run_cypher(cypher, query_params, limit)

            return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error("Neo4j action failed action=%s type=%s", action, type(e).__name__)
            return {"success": False, "error": "Neo4j request failed"}
        finally:
            if driver is not None:
                await self._close_driver(driver)
