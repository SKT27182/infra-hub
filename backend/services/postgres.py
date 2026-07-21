"""
PostgreSQL service implementation.
"""

import asyncio
import re
from typing import Any

import asyncpg

from config import settings
from utils.logger import create_logger

from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)
DATABASE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,62}$")


class PostgresService(BaseService):
    """PostgreSQL database service."""

    name = settings.postgres_service_name
    display_name = settings.postgres_display_name
    container_name = settings.postgres_container_name
    admin_url = settings.postgres_admin_url
    admin_container = settings.pgadmin_container_name

    async def get_info(self) -> dict[str, Any]:
        """Get PostgreSQL information including databases, connections, and version."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            databases = await conn.fetch(
                "SELECT datname as name, pg_database_size(datname) as size FROM pg_database WHERE datistemplate = false LIMIT 501"
            )
            stats = await conn.fetchrow(
                "SELECT count(*) as active FROM pg_stat_activity WHERE state = 'active'"
            )
            max_conn = await conn.fetchval("SHOW max_connections")
            version = await conn.fetchval("SHOW server_version")
            await conn.close()

            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.postgres_admin_url,
                    instructions=[
                        "Open pgAdmin and sign in with PGADMIN_EMAIL and PGADMIN_PASSWORD from backend/.env.",
                        "Register a server pointing at host port POSTGRES_PORT with POSTGRES_USER credentials.",
                    ],
                    login={
                        "email_env": "PGADMIN_EMAIL",
                        "password_env": "PGADMIN_PASSWORD",
                    },
                ),
                "connection": {
                    "url": f"postgresql://{settings.service_public_host}:{settings.postgres_port}/{settings.postgres_db}",
                    "host": settings.service_public_host,
                    "port": settings.postgres_port,
                    "user": settings.postgres_user,
                    "password_env": "POSTGRES_PASSWORD",
                },
                "databases": [
                    {"name": db["name"], "size": db["size"]} for db in databases
                ][:500],
                "databases_truncated": len(databases) > 500,
                "active_connections": stats["active"] if stats else 0,
                "max_connections": int(max_conn) if max_conn else 100,
                "version": version or "unknown",
            }
        except Exception as e:
            logger.warning("Postgres get_info failed (%s)", type(e).__name__)
            return {"error": "PostgreSQL information is unavailable", "status": self.get_status().model_dump()}

    async def create_database(self, name: str) -> bool:
        """Create a new database."""
        if not DATABASE_NAME_RE.fullmatch(name):
            return False
        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            await conn.execute(f'CREATE DATABASE "{name}"')
            return True
        except Exception:
            return False
        finally:
            if conn is not None:
                await conn.close()

    async def query(self, query: str, database: str | None = None) -> dict[str, Any]:
        """Run one privileged SQL statement with bounded execution and output."""
        sql = query.strip()
        target_db = (database or settings.postgres_db).strip()

        if not sql:
            return {"success": False, "error": "Query cannot be empty"}

        if ";" in sql.rstrip(";"):
            return {
                "success": False,
                "error": "Only a single SQL statement is allowed",
            }

        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=target_db,
            )
            await conn.execute("SET statement_timeout = '10s'")
            statement = await asyncio.wait_for(conn.prepare(sql), timeout=10)
            if statement.get_attributes():
                async with conn.transaction():
                    cursor = statement.cursor()
                    rows = await asyncio.wait_for(cursor.fetch(501), timeout=10)
                truncated = len(rows) > 500
                rows = rows[:500]
                command = None
            else:
                command = await asyncio.wait_for(conn.execute(sql), timeout=10)
                rows = []
                truncated = False

            return {
                "success": True,
                "database": target_db,
                "row_count": len(rows),
                "truncated": truncated,
                "command": command,
                "columns": list(rows[0].keys()) if rows else [],
                "rows": [dict(row) for row in rows],
            }
        except TimeoutError:
            return {"success": False, "error": "Query timed out", "database": target_db}
        except Exception as e:
            logger.error("Postgres query failed on %s (%s)", target_db, type(e).__name__)
            return {"success": False, "error": "Query failed", "database": target_db}
        finally:
            if conn is not None:
                await conn.close()

    async def drop_database(self, name: str) -> bool:
        """Drop an existing database."""
        if not DATABASE_NAME_RE.fullmatch(name):
            return False
        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            await conn.execute(f'DROP DATABASE "{name}"')
            return True
        except Exception:
            return False
        finally:
            if conn is not None:
                await conn.close()
