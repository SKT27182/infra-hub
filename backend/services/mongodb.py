"""
MongoDB service implementation.
"""

import json
from typing import Any

from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from utils.logger import create_logger

from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)


class MongoDBService(BaseService):
    """MongoDB document database service."""

    name = settings.mongodb_service_name
    display_name = settings.mongodb_display_name
    container_name = settings.mongodb_container_name
    admin_url = settings.mongodb_admin_url
    admin_container = settings.mongo_express_container_name

    def _get_client(self) -> AsyncIOMotorClient[dict[str, Any]]:
        timeout_ms = int(settings.service_request_timeout_seconds * 1000)
        return AsyncIOMotorClient(
            settings.mongo_url,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            socketTimeoutMS=timeout_ms,
        )

    async def get_info(self) -> dict[str, Any]:
        """Get MongoDB information including databases, collections, and version."""
        try:
            client = self._get_client()
            databases = await client.list_database_names()
            db_details = []
            total_collections = 0
            for db_name in databases[:500]:
                if db_name not in ["admin", "config", "local"]:
                    stats = await client[db_name].command("dbStats")
                    colls = stats.get("collections", 0)
                    total_collections += colls
                    db_details.append(
                        {
                            "name": db_name,
                            "size": stats.get("dataSize", 0),
                            "collections": colls,
                        }
                    )
            server_info = await client.server_info()
            client.close()

            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.mongodb_admin_url,
                    instructions=[
                        "Open Mongo Express to browse databases and collections.",
                        "Basic auth is disabled in local compose (ME_CONFIG_BASICAUTH=false).",
                    ],
                ),
                "connection": {
                    "url": f"mongodb://{settings.service_public_host}:{settings.mongo_port}"
                },
                "databases": db_details,
                "databases_truncated": len(databases) > 500,
                "total_collections": total_collections,
                "version": server_info.get("version", "unknown"),
            }
        except Exception as e:
            logger.warning("MongoDB get_info failed (%s)", type(e).__name__)
            return {"error": "MongoDB information is unavailable", "status": self.get_status().model_dump()}

    async def drop_database(self, name: str) -> bool:
        """Drop a database."""
        try:
            client = self._get_client()
            await client.drop_database(name)
            client.close()
            return True
        except Exception:
            return False

    async def query(
        self, action: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute read-oriented MongoDB queries."""
        payload = params or {}
        client = self._get_client()

        try:
            if action == "list_databases":
                names = await client.list_database_names()
                return {"success": True, "result": names}

            database = str(payload.get("database") or "").strip()
            if not database:
                return {"success": False, "error": "database is required"}

            db = client[database]

            if action == "list_collections":
                names = await db.list_collection_names()
                return {"success": True, "result": names}

            collection_name = str(payload.get("collection") or "").strip()
            if not collection_name:
                return {"success": False, "error": "collection is required"}

            collection = db[collection_name]

            if action == "find":
                filter_doc = payload.get("filter") or {}
                projection = payload.get("projection")
                limit = max(1, min(int(payload.get("limit", 20)), 500))
                offset = max(0, min(int(payload.get("offset", 0)), 1_000_000))
                sort = payload.get("sort")

                cursor = collection.find(filter_doc, projection)
                if sort:
                    cursor = cursor.sort(sort)
                docs = await cursor.skip(offset).limit(limit + 1).to_list(length=limit + 1)
                return {
                    "success": True,
                    "count": min(len(docs), limit),
                    "result": json.loads(json_util.dumps(docs[:limit])),
                    "offset": offset,
                    "page_size": limit,
                    "truncated": len(docs) > limit,
                    "next_offset": offset + limit if len(docs) > limit else None,
                }

            if action == "count":
                filter_doc = payload.get("filter") or {}
                count = await collection.count_documents(filter_doc)
                return {"success": True, "result": count}

            return {"success": False, "error": f"Unsupported action: {action}"}
        except Exception as e:
            logger.error("MongoDB query failed action=%s type=%s", action, type(e).__name__)
            return {"success": False, "error": "MongoDB query failed"}
        finally:
            client.close()
