"""
PostgreSQL service implementation.
"""

import re
from typing import Any

import asyncpg

from config import settings
from .base import BaseService


class PostgresService(BaseService):
    """PostgreSQL database service."""

    name = "postgres"
    display_name = "PostgreSQL"
    container_name = "infra-postgres"
    admin_url = "http://localhost:5050"
    admin_container = "infra-pgadmin"
    _readonly_query_pattern = re.compile(
        r"^\s*(select|with|show|explain)\b",
        re.IGNORECASE,
    )

    async def get_info(self) -> dict[str, Any]:
        """Get PostgreSQL information including databases, connections, and version."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            databases = await conn.fetch(
                "SELECT datname as name, pg_database_size(datname) as size FROM pg_database WHERE datistemplate = false"
            )
            stats = await conn.fetchrow(
                "SELECT count(*) as active FROM pg_stat_activity WHERE state = 'active'"
            )
            max_conn = await conn.fetchval("SHOW max_connections")
            version = await conn.fetchval("SHOW server_version")
            await conn.close()

            return {
                "status": self.get_status().model_dump(),
                "connection": {
                    "url": f"postgresql://{settings.postgres_user}:{settings.postgres_password}@127.0.0.1:{settings.postgres_port}",
                    "host": "127.0.0.1",
                    "port": settings.postgres_port,
                    "user": settings.postgres_user,
                    "password": settings.postgres_password,
                },
                "databases": [
                    {"name": db["name"], "size": db["size"]} for db in databases
                ],
                "active_connections": stats["active"] if stats else 0,
                "max_connections": int(max_conn) if max_conn else 100,
                "version": version or "unknown",
            }
        except Exception as e:
            return {"error": str(e), "status": self.get_status().model_dump()}

    async def create_database(self, name: str) -> bool:
        """Create a new database."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            await conn.execute(f'CREATE DATABASE "{name}"')
            await conn.close()
            return True
        except Exception:
            return False

    async def query(self, query: str, database: str | None = None) -> dict[str, Any]:
        """Run a read-only SQL query against PostgreSQL."""
        sql = query.strip()
        target_db = (database or settings.postgres_db).strip()

        if not sql:
            return {"success": False, "error": "Query cannot be empty"}

        if ";" in sql.rstrip(";"):
            return {
                "success": False,
                "error": "Only a single SQL statement is allowed",
            }

        if not self._readonly_query_pattern.match(sql):
            return {
                "success": False,
                "error": "Only read-only queries are allowed (SELECT/WITH/SHOW/EXPLAIN)",
            }

        try:
            conn = await asyncpg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=target_db,
            )
            rows = await conn.fetch(sql)
            await conn.close()

            return {
                "success": True,
                "database": target_db,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows else [],
                "rows": [dict(row) for row in rows],
            }
        except Exception as e:
            return {"success": False, "error": str(e), "database": target_db}

    async def drop_database(self, name: str) -> bool:
        """Drop an existing database."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            await conn.execute(f'DROP DATABASE "{name}"')
            await conn.close()
            return True
        except Exception:
            return False
