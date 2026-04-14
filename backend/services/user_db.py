"""
User database service handling user storage in PostgreSQL.
"""

import logging
from typing import Any

import asyncpg

from config import settings
from .auth import auth_service

logger = logging.getLogger(__name__)


class UserStoreUnavailableError(RuntimeError):
    """Raised when the user store cannot be reached."""


class UserService:
    """Service to manage users in PostgreSQL."""

    def __init__(self) -> None:
        """Initialize the user service."""
        pass

    async def ensure_user_table(self) -> None:
        """Create the users table if it doesn't exist."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.close()
        except Exception as e:
            print(f"Error creating user table: {e}")

    async def create_user(
        self, email: str, password: str, full_name: str | None = None
    ) -> dict[str, Any] | None:
        """Create a new user."""
        hashed_password = auth_service.get_password_hash(password)
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            user = await conn.fetchrow(
                """
                INSERT INTO users (email, hashed_password, full_name)
                VALUES ($1, $2, $3)
                RETURNING id, email, full_name, is_active, created_at
                """,
                email,
                hashed_password,
                full_name,
            )
            await conn.close()
            return dict(user) if user else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Fetch a user by email."""
        try:
            conn = await asyncpg.connect(settings.postgres_url)
            user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            await conn.close()
            return dict(user) if user else None
        except (asyncpg.PostgresError, OSError) as exc:
            logger.exception("Error fetching user by email")
            raise UserStoreUnavailableError("User database is unavailable") from exc


user_service = UserService()
