"""Role-free Infra Hub v2 user storage."""

from collections.abc import Mapping
from typing import Any

import asyncpg

from config import settings
from utils.logger import create_logger

logger = create_logger(__name__, level=settings.log_level)


class UserStoreUnavailableError(RuntimeError):
    """Raised when the user store cannot be reached."""


class UserService:
    """Manage equally privileged infrastructure administrators."""

    async def _connect(self) -> asyncpg.Connection:
        return await asyncpg.connect(settings.postgres_url)

    async def ensure_schema(self) -> None:
        """Create the v2 user schema for a fresh database when absent."""
        conn = await self._connect()
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    auth_version INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_unique ON users (lower(email))"
            )
        except (asyncpg.PostgresError, OSError) as exc:
            logger.exception("User schema initialization failed")
            raise UserStoreUnavailableError("User schema initialization failed") from exc
        finally:
            await conn.close()

    async def ensure_default_admin_user(self) -> None:
        """Insert the configured initial admin without modifying an existing row."""
        from services.auth import auth_service

        conn = await self._connect()
        email = settings.admin_email.strip().lower()
        try:
            async with conn.transaction():
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtext('infra-hub-bootstrap'))"
                )
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE lower(email) = $1)",
                    email,
                )
                if exists:
                    logger.info("Default infra admin already exists")
                    return
                result = await conn.execute(
                    """
                    INSERT INTO users (email, hashed_password, name, is_active)
                    VALUES ($1, $2, $3, TRUE)
                    ON CONFLICT DO NOTHING
                    """,
                    email,
                    auth_service.get_password_hash(settings.admin_password),
                    email.split("@", 1)[0],
                )
                logger.info(
                    "Default infra admin %s",
                    "created" if result == "INSERT 0 1" else "already exists",
                )
        finally:
            await conn.close()

    @staticmethod
    def public_user(row: Mapping[str, Any]) -> dict[str, Any]:
        """Remove authentication-only fields from a user record."""
        data = dict(row)
        data.pop("hashed_password", None)
        data.pop("auth_version", None)
        return data

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Return a public user record by id."""
        conn = await self._connect()
        try:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return self.public_user(row) if row else None
        except (asyncpg.PostgresError, OSError) as exc:
            raise UserStoreUnavailableError("User database is unavailable") from exc
        finally:
            await conn.close()

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Return an authentication record using case-insensitive email lookup."""
        conn = await self._connect()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE lower(email) = lower($1)", email.strip()
            )
            return dict(row) if row else None
        except (asyncpg.PostgresError, OSError) as exc:
            raise UserStoreUnavailableError("User database is unavailable") from exc
        finally:
            await conn.close()

    async def update_profile(self, user_id: int, name: str) -> dict[str, Any] | None:
        """Update the current user's display name."""
        conn = await self._connect()
        try:
            row = await conn.fetchrow(
                """
                UPDATE users SET name = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                RETURNING *
                """,
                name.strip(),
                user_id,
            )
            return self.public_user(row) if row else None
        finally:
            await conn.close()

    async def change_password(self, user_id: int, hashed_password: str) -> bool:
        """Change a password and revoke every existing session."""
        conn = await self._connect()
        try:
            result = await conn.execute(
                """
                UPDATE users SET hashed_password = $1,
                    auth_version = auth_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                hashed_password,
                user_id,
            )
            return bool(result == "UPDATE 1")
        finally:
            await conn.close()


user_service = UserService()
