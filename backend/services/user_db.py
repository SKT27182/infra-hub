"""
User database service handling user storage in PostgreSQL.
"""

from enum import Enum
from typing import Any

import asyncpg

from config import settings
from utils.logger import create_logger
from .auth import auth_service

logger = create_logger(__name__, level=settings.log_level)


class UserStoreUnavailableError(RuntimeError):
    """Raised when the user store cannot be reached."""


class InfraUserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    USER = "USER"


class UserService:
    """Service to manage users in PostgreSQL."""

    async def _connect(self) -> asyncpg.Connection:
        return await asyncpg.connect(settings.postgres_url)

    async def ensure_user_table(self) -> None:
        """Create the users table if it doesn't exist."""
        try:
            conn = await self._connect()
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    role VARCHAR(32) NOT NULL DEFAULT 'USER',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role VARCHAR(32) NOT NULL DEFAULT 'USER'
                """
            )
            await conn.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE
                DEFAULT CURRENT_TIMESTAMP
                """
            )
            await conn.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'users' AND column_name = 'full_name'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'users' AND column_name = 'name'
                    ) THEN
                        ALTER TABLE users RENAME COLUMN full_name TO name;
                    END IF;
                END
                $$;
                """
            )
            await conn.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS name VARCHAR(255)
                """
            )
            await conn.execute(
                """
                UPDATE users SET name = split_part(email, '@', 1)
                WHERE name IS NULL OR name = ''
                """
            )
            await conn.close()
            logger.info("User table ensured")
        except Exception:
            logger.exception("Error creating user table")
            raise

    async def ensure_default_admin_user(self) -> None:
        """Create or update the default admin user from env settings."""
        try:
            conn = await self._connect()
            hashed_password = auth_service.get_password_hash(settings.admin_password)
            await conn.execute(
                """
                INSERT INTO users (email, hashed_password, name, role, is_active)
                VALUES ($1, $2, $3, $4, TRUE)
                ON CONFLICT (email)
                DO UPDATE SET
                    hashed_password = EXCLUDED.hashed_password,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    is_active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                """,
                settings.admin_email,
                hashed_password,
                "ADMIN",
                InfraUserRole.SUPER_ADMIN.value,
            )
            await conn.close()
            logger.info("Default admin user ensured: %s", settings.admin_email)
        except Exception:
            logger.exception("Error ensuring default admin user")
            raise

    def _row_to_dict(self, row: asyncpg.Record) -> dict[str, Any]:
        data = dict(row)
        if "hashed_password" in data:
            del data["hashed_password"]
        if data.get("role") is None:
            data["role"] = InfraUserRole.USER.value
        if not data.get("name"):
            email = data.get("email") or ""
            data["name"] = email.split("@", 1)[0] if email else "User"
        return data

    async def list_users(self) -> list[dict[str, Any]]:
        try:
            conn = await self._connect()
            rows = await conn.fetch(
                """
                SELECT id, email, name, role, is_active, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
                """
            )
            await conn.close()
            return [self._row_to_dict(r) for r in rows]
        except (asyncpg.PostgresError, OSError) as exc:
            logger.exception("Error listing users")
            raise UserStoreUnavailableError("User database is unavailable") from exc

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        try:
            conn = await self._connect()
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            await conn.close()
            return self._row_to_dict(row) if row else None
        except (asyncpg.PostgresError, OSError) as exc:
            logger.exception("Error fetching user by id")
            raise UserStoreUnavailableError("User database is unavailable") from exc

    async def create_user(
        self,
        email: str,
        password: str,
        name: str | None = None,
        role: str = InfraUserRole.USER.value,
    ) -> dict[str, Any] | None:
        """Create a new user."""
        if role == InfraUserRole.SUPER_ADMIN.value:
            raise ValueError("Cannot create SUPER_ADMIN via API")

        display_name = (name or email.split("@", 1)[0]).strip() or "User"
        hashed_password = auth_service.get_password_hash(password)
        try:
            conn = await self._connect()
            user = await conn.fetchrow(
                """
                INSERT INTO users (email, hashed_password, name, role)
                VALUES ($1, $2, $3, $4)
                RETURNING id, email, name, role, is_active, created_at, updated_at
                """,
                email,
                hashed_password,
                display_name,
                role,
            )
            await conn.close()
            if user:
                logger.info("User created: %s", email)
            return dict(user) if user else None
        except asyncpg.UniqueViolationError:
            logger.debug("User create rejected: email already exists")
            return None
        except Exception as e:
            logger.exception("Error creating user")
            return None

    async def update_user(
        self,
        user_id: int,
        *,
        name: str | None = None,
        password: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        touch_updated: bool = False,
    ) -> dict[str, Any] | None:
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        updates: list[str] = []
        values: list[Any] = []
        idx = 1

        if name is not None:
            updates.append(f"name = ${idx}")
            values.append(name.strip())
            idx += 1
            touch_updated = True
        if password is not None:
            updates.append(f"hashed_password = ${idx}")
            values.append(auth_service.get_password_hash(password))
            idx += 1
            touch_updated = True
        if role is not None:
            if role == InfraUserRole.SUPER_ADMIN.value:
                raise ValueError("Cannot assign SUPER_ADMIN via API")
            updates.append(f"role = ${idx}")
            values.append(role)
            idx += 1
        if is_active is not None:
            updates.append(f"is_active = ${idx}")
            values.append(is_active)
            idx += 1

        if not updates:
            return user

        if touch_updated:
            updates.append("updated_at = CURRENT_TIMESTAMP")

        values.append(user_id)
        try:
            conn = await self._connect()
            row = await conn.fetchrow(
                f"""
                UPDATE users SET {", ".join(updates)}
                WHERE id = ${idx}
                RETURNING id, email, name, role, is_active, created_at, updated_at
                """,
                *values,
            )
            await conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.exception("Error updating user")
            return None

    async def delete_user(self, user_id: int) -> bool:
        try:
            conn = await self._connect()
            result = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
            await conn.close()
            return result == "DELETE 1"
        except Exception as e:
            logger.exception("Error deleting user")
            return False

    async def count_super_admins(self, exclude_id: int | None = None) -> int:
        try:
            conn = await self._connect()
            if exclude_id is not None:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM users
                    WHERE role = $1 AND is_active = TRUE AND id != $2
                    """,
                    InfraUserRole.SUPER_ADMIN.value,
                    exclude_id,
                )
            else:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM users WHERE role = $1 AND is_active = TRUE",
                    InfraUserRole.SUPER_ADMIN.value,
                )
            await conn.close()
            return int(count or 0)
        except Exception:
            return 0

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Fetch a user by email (includes hashed_password for auth)."""
        try:
            conn = await self._connect()
            user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            await conn.close()
            if not user:
                return None
            data = dict(user)
            if data.get("role") is None:
                data["role"] = InfraUserRole.USER.value
            return data
        except (asyncpg.PostgresError, OSError) as exc:
            logger.exception("Error fetching user by email")
            raise UserStoreUnavailableError("User database is unavailable") from exc


user_service = UserService()
