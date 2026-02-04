"""
MongoDB service implementation.
"""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.services.base import BaseService, ServiceHealth


class MongoDBService(BaseService):
    """MongoDB document database service."""

    name = "mongodb"
    display_name = "MongoDB"
    container_name = "infra-mongodb"
    admin_url = "http://localhost:8081"
    admin_container = "infra-mongo-express"

    def _get_client(self) -> AsyncIOMotorClient:  # type: ignore
        """Get MongoDB client."""
        return AsyncIOMotorClient(settings.mongo_url)

    async def check_health(self) -> ServiceHealth:
        """Check MongoDB connectivity."""
        try:
            client = self._get_client()
            result = await client.admin.command("ping")
            server_info = await client.server_info()
            client.close()
            return ServiceHealth(
                healthy=result.get("ok") == 1,
                message="MongoDB is responding",
                details={"version": server_info.get("version")},
            )
        except Exception as e:
            return ServiceHealth(
                healthy=False,
                message=f"MongoDB connection failed: {e}",
            )

    async def get_info(self) -> dict[str, Any]:
        """Get MongoDB server information."""
        try:
            client = self._get_client()

            # Get server info
            server_info = await client.server_info()

            # Get database list
            databases = await client.list_database_names()
            db_details = []
            for db_name in databases:
                if db_name not in ["admin", "config", "local"]:
                    stats = await client[db_name].command("dbStats")
                    db_details.append(
                        {
                            "name": db_name,
                            "size": stats.get("dataSize", 0),
                            "collections": stats.get("collections", 0),
                        }
                    )

            client.close()

            return {
                "version": server_info.get("version"),
                "databases": db_details,
                "total_databases": len(db_details),
            }
        except Exception as e:
            return {"error": str(e)}

    async def list_databases(self) -> list[dict[str, Any]]:
        """List all databases with details."""
        try:
            client = self._get_client()
            databases = []

            for db_name in await client.list_database_names():
                if db_name not in ["admin", "config", "local"]:
                    stats = await client[db_name].command("dbStats")
                    databases.append(
                        {
                            "name": db_name,
                            "size": stats.get("dataSize", 0),
                            "storage_size": stats.get("storageSize", 0),
                            "collections": stats.get("collections", 0),
                            "indexes": stats.get("indexes", 0),
                        }
                    )

            client.close()
            return databases
        except Exception as e:
            return [{"error": str(e)}]

    async def list_collections(self, database: str) -> list[dict[str, Any]]:
        """List collections in a database."""
        try:
            client = self._get_client()
            db = client[database]
            collections = []

            for coll_name in await db.list_collection_names():
                stats = await db.command("collStats", coll_name)
                collections.append(
                    {
                        "name": coll_name,
                        "count": stats.get("count", 0),
                        "size": stats.get("size", 0),
                        "avg_obj_size": stats.get("avgObjSize", 0),
                        "indexes": stats.get("nindexes", 0),
                    }
                )

            client.close()
            return collections
        except Exception as e:
            return [{"error": str(e)}]
