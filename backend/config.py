"""
Application configuration using pydantic-settings.
"""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8888
    debug: bool = False
    service_public_host: str = "127.0.0.1"
    admin_email: str = "admin@infra.local"
    admin_password: str = "admin12345"

    # CORS
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5143"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        """Allow CORS origins as a JSON array or comma-separated string."""
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            if raw.startswith("["):
                parsed = json.loads(raw)
                return [
                    origin.strip()
                    for origin in parsed
                    if isinstance(origin, str) and origin.strip()
                ]

            return [origin.strip() for origin in raw.split(",") if origin.strip()]

        msg = "cors_origins must be a list or string"
        raise TypeError(msg)

    # PostgreSQL
    postgres_service_name: str = "postgres"
    postgres_display_name: str = "PostgreSQL"
    postgres_container_name: str = "infra-postgres"
    pgadmin_container_name: str = "infra-pgadmin"
    pgadmin_port: int = 5050
    postgres_host: str = "localhost"
    postgres_port: int = 54321
    postgres_user: str = "admin"
    postgres_password: str = "password"
    postgres_db: str = "main_db"

    # Redis
    redis_service_name: str = "redis"
    redis_display_name: str = "Redis"
    redis_container_name: str = "infra-redis"
    redisinsight_container_name: str = "infra-redisinsight"
    redisinsight_port: int = 5540
    redis_host: str = "localhost"
    redis_port: int = 63791
    redis_password: str = "password"

    # MongoDB
    mongodb_service_name: str = "mongodb"
    mongodb_display_name: str = "MongoDB"
    mongodb_container_name: str = "infra-mongodb"
    mongo_express_container_name: str = "infra-mongo-express"
    mongo_express_port: int = 8081
    mongo_host: str = "localhost"
    mongo_port: int = 27018
    mongo_user: str = "admin"
    mongo_password: str = "password"

    # Qdrant
    qdrant_service_name: str = "qdrant"
    qdrant_display_name: str = "Qdrant"
    qdrant_container_name: str = "infra-qdrant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None

    # MinIO
    minio_service_name: str = "minio"
    minio_display_name: str = "MinIO"
    minio_container_name: str = "infra-minio"
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_console_port: int = 9001
    minio_user: str = "admin"
    minio_password: str = "adminadmin"

    # JWT Authentication
    jwt_secret: str = "secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    @property
    def postgres_url(self) -> str:
        """PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"

    @property
    def mongo_url(self) -> str:
        """MongoDB connection URL."""
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}"
        )

    @property
    def minio_endpoint(self) -> str:
        """MinIO endpoint."""
        return f"{self.minio_host}:{self.minio_port}"

    @property
    def postgres_admin_url(self) -> str:
        """pgAdmin URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.pgadmin_port}"

    @property
    def redis_admin_url(self) -> str:
        """RedisInsight URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.redisinsight_port}"

    @property
    def mongodb_admin_url(self) -> str:
        """Mongo Express URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.mongo_express_port}"

    @property
    def qdrant_admin_url(self) -> str:
        """Qdrant dashboard URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.qdrant_port}/dashboard"

    @property
    def minio_admin_url(self) -> str:
        """MinIO console URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.minio_console_port}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
