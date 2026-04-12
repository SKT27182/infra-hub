"""
Application configuration using pydantic-settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8888
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 54321
    postgres_user: str = "admin"
    postgres_password: str = "password"
    postgres_db: str = "main_db"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 63791
    redis_password: str = "password"

    # MongoDB
    mongo_host: str = "localhost"
    mongo_port: int = 27018
    mongo_user: str = "admin"
    mongo_password: str = "password"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None

    # MinIO
    minio_host: str = "localhost"
    minio_port: int = 9000
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


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
