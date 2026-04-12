"""
MongoDB service implementation.
"""

import json
from typing import Any

from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from .base import BaseService


class MongoDBService(BaseService):
    """MongoDB document database service."""

    name = "mongodb"
    display_name = "MongoDB"
    container_name = "infra-mongodb"
    admin_url = "http://localhost:8081"
    admin_container = "infra-mongo-express"

    def _get_client(self) -> AsyncIOMotorClient:
        return AsyncIOMotorClient(settings.mongo_url)

    async def get_info(self) -> dict[str, Any]:
        """Get MongoDB information including databases, collections, and version."""
        try:
            client = self._get_client()
            databases = await client.list_database_names()
            db_details = []
            total_collections = 0
            for db_name in databases:
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
                "connection": {"url": f"mongodb://127.0.0.1:{settings.mongo_port}"},
                "databases": db_details,
                "total_collections": total_collections,
                "version": server_info.get("version", "unknown"),
            }
        except Exception as e:
            return {"error": str(e), "status": self.get_status().model_dump()}

    async def drop_database(self, name: str) -> bool:
        """Drop a database."""
        try:
            client = self._get_client()
            await client.drop_database(name)
            client.close()
            return True
        except Exception:
            return False

    async def query(self, action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
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
                limit = int(payload.get("limit", 20))
                sort = payload.get("sort")

                cursor = collection.find(filter_doc, projection)
                if sort:
                    cursor = cursor.sort(sort)
                docs = await cursor.limit(limit).to_list(length=limit)
                return {
                    "success": True,
                    "count": len(docs),
                    "result": json.loads(json_util.dumps(docs)),
                }

            if action == "count":
                filter_doc = payload.get("filter") or {}
                count = await collection.count_documents(filter_doc)
                return {"success": True, "result": count}

            return {"success": False, "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            client.close()
