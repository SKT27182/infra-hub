"""
PostgreSQL service implementation.
"""

from typing import Any

import asyncpg

from app.core.config import settings
from app.services.base import BaseService, ServiceHealth


class PostgresService(BaseService):
    """PostgreSQL database service."""

    name = "postgres"
    display_name = "PostgreSQL"
    container_name = "infra-postgres"
    admin_url = "http://localhost:5050"
    admin_container = "infra-pgadmin"

    async def check_health(self) -> ServiceHealth:
        """Check PostgreSQL connectivity."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            return ServiceHealth(
                healthy=True,
                message="PostgreSQL is responding",
                details={"version": version},
            )
        except Exception as e:
            return ServiceHealth(
                healthy=False,
                message=f"PostgreSQL connection failed: {e}",
            )

    async def get_info(self) -> dict[str, Any]:
        """Get PostgreSQL server information."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)

            # Get version
            version = await conn.fetchval("SELECT version()")

            # Get database list
            databases = await conn.fetch(
                """
                SELECT datname, pg_database_size(datname) as size
                FROM pg_database
                WHERE datistemplate = false
                ORDER BY datname
                """
            )

            # Get connection stats
            connections = await conn.fetchval("SELECT count(*) FROM pg_stat_activity")

            await conn.close()

            return {
                "version": version,
                "databases": [
                    {"name": db["datname"], "size": db["size"]} for db in databases
                ],
                "active_connections": connections,
            }
        except Exception as e:
            return {"error": str(e)}

    async def list_databases(self) -> list[dict[str, Any]]:
        """List all databases with details."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            databases = await conn.fetch(
                """
                SELECT
                    datname as name,
                    pg_database_size(datname) as size,
                    datcollate as collation,
                    datconnlimit as connection_limit
                FROM pg_database
                WHERE datistemplate = false
                ORDER BY datname
                """
            )
            await conn.close()
            return [dict(db) for db in databases]
        except Exception as e:
            return [{"error": str(e)}]

    async def list_tables(self, database: str) -> list[dict[str, Any]]:
        """List tables in a database."""
        try:
            url = settings.postgres_url.rsplit("/", 1)[0] + f"/{database}"
            conn = await asyncpg.connect(url)
            tables = await conn.fetch(
                """
                SELECT
                    schemaname as schema,
                    tablename as name,
                    pg_total_relation_size(schemaname || '.' || tablename) as size
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
                """
            )
            await conn.close()
            return [dict(t) for t in tables]
        except Exception as e:
            return [{"error": str(e)}]
