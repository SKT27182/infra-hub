"""
Application configuration using pydantic-settings.
"""

import json
from functools import lru_cache
from ipaddress import ip_address
from typing import Annotated
from urllib.parse import quote, urlparse

from pydantic import EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Settings
    api_host: str = "127.0.0.1"
    api_port: int = 8888
    debug: bool = False
    log_level: str = "INFO"
    app_public_url: str | None = None
    app_public_host: str | None = None
    service_public_host: str = "127.0.0.1"
    service_bind_host: str = "127.0.0.1"
    host_only_mode: bool = True
    max_request_body_bytes: int = 1024 * 1024
    service_request_timeout_seconds: float = 10.0
    admin_email: EmailStr
    admin_password: str

    # CORS (local dev origins; APP_PUBLIC_URL is merged in automatically)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5143", "http://127.0.0.1:5143"]

    @model_validator(mode="after")
    def apply_public_app_settings(self) -> "Settings":
        if self.app_public_host:
            self.service_public_host = self.app_public_host
        elif self.app_public_url:
            hostname = urlparse(self.app_public_url).hostname
            if hostname:
                self.service_public_host = hostname
        if self.app_public_url:
            public_origin = self.app_public_url.rstrip("/")
            if public_origin not in self.cors_origins:
                self.cors_origins.append(public_origin)
            if urlparse(self.app_public_url).scheme == "https":
                self.auth_cookie_secure = True
        return self

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
    pgadmin_password: str
    # Docker publishes the database on the IPv4 loopback by default. Using the
    # hostname can resolve to ::1 first, where an unrelated local process may
    # be listening even though 127.0.0.1 is correctly mapped to PostgreSQL.
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 54321
    postgres_user: str
    postgres_password: str
    postgres_db: str = "main_db"

    # Redis
    redis_service_name: str = "redis"
    redis_display_name: str = "Redis"
    redis_container_name: str = "infra-redis"
    redisinsight_container_name: str = "infra-redisinsight"
    redisinsight_port: int = 5540
    redis_host: str = "localhost"
    redis_port: int = 63791
    redis_password: str

    # MongoDB
    mongodb_service_name: str = "mongodb"
    mongodb_display_name: str = "MongoDB"
    mongodb_container_name: str = "infra-mongodb"
    mongo_express_container_name: str = "infra-mongo-express"
    mongo_express_port: int = 8081
    mongo_host: str = "localhost"
    mongo_port: int = 27018
    mongo_user: str
    mongo_password: str

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
    minio_user: str
    minio_password: str

    # Neo4j (Community Edition requires username neo4j — set NEO4J_USER in .env)
    neo4j_service_name: str = "neo4j"
    neo4j_display_name: str = "Neo4j"
    neo4j_container_name: str = "infra-neo4j"
    neo4j_host: str = "localhost"
    neo4j_http_port: int = 7474
    neo4j_bolt_port: int = 7687
    neo4j_user: str
    neo4j_password: str

    # OpenSearch
    opensearch_service_name: str = "opensearch"
    opensearch_display_name: str = "OpenSearch"
    opensearch_container_name: str = "infra-opensearch"
    opensearch_dashboards_container_name: str = "infra-opensearch-dashboards"
    opensearch_host: str = "localhost"
    opensearch_http_port: int = 9200
    opensearch_dashboards_port: int = 5601

    # JWT Authentication
    jwt_secret: str
    session_lifetime_minutes: int = 60 * 8
    auth_cookie_name: str = "infra_hub_session"
    auth_cookie_secure: bool = False
    jwt_issuer: str = "infra-hub"
    jwt_audience: str = "infra-hub-ui"

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        """Reject unsafe networking and signing configuration."""
        if self.host_only_mode:
            for field_name, host in (
                ("api_host", self.api_host),
                ("service_bind_host", self.service_bind_host),
            ):
                try:
                    if not ip_address(host).is_loopback:
                        raise ValueError(f"{field_name} must be loopback in host-only mode")
                except ValueError as exc:
                    if "must be loopback" in str(exc):
                        raise
                    raise ValueError(f"{field_name} must be an IP address") from exc
        try:
            service_is_loopback = ip_address(self.service_bind_host).is_loopback
        except ValueError as exc:
            raise ValueError("SERVICE_BIND_HOST must be an IP address") from exc
        if not service_is_loopback:
            raise ValueError(
                "OpenSearch and Mongo Express security is disabled; SERVICE_BIND_HOST must remain loopback"
            )
        if len(self.jwt_secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 bytes")
        placeholders = {
            "changeme",
            "replace-with-a-unique-strong-password",
            "replace-with-at-least-32-random-bytes",
        }
        if self.admin_password.lower() in placeholders:
            raise ValueError("ADMIN_PASSWORD must not be a documented placeholder")
        if len(self.admin_password.encode("utf-8")) > 72:
            raise ValueError("ADMIN_PASSWORD must be at most 72 UTF-8 bytes")
        if self.jwt_secret.lower() in placeholders:
            raise ValueError("JWT_SECRET must not be a documented placeholder")
        service_credentials = {
            "POSTGRES_PASSWORD": self.postgres_password,
            "PGADMIN_PASSWORD": self.pgadmin_password,
            "REDIS_PASSWORD": self.redis_password,
            "MONGO_PASSWORD": self.mongo_password,
            "MINIO_PASSWORD": self.minio_password,
            "NEO4J_PASSWORD": self.neo4j_password,
        }
        if self.qdrant_api_key:
            service_credentials["QDRANT_API_KEY"] = self.qdrant_api_key
        for field_name, credential in service_credentials.items():
            normalized = credential.strip().lower()
            if (
                normalized.startswith("replace-with-")
                or normalized.startswith("generate-")
            ):
                raise ValueError(f"{field_name} must not be a documented placeholder")
        return self

    @property
    def postgres_url(self) -> str:
        """PostgreSQL connection URL."""
        return (
            f"postgresql://{quote(self.postgres_user, safe='')}:{quote(self.postgres_password, safe='')}"
            f"@{self.postgres_host}:{self.postgres_port}/{quote(self.postgres_db, safe='')}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://:{quote(self.redis_password, safe='')}@{self.redis_host}:{self.redis_port}"

    @property
    def mongo_url(self) -> str:
        """MongoDB connection URL."""
        return (
            f"mongodb://{quote(self.mongo_user, safe='')}:{quote(self.mongo_password, safe='')}"
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

    @property
    def neo4j_admin_url(self) -> str:
        """Neo4j Browser URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.neo4j_http_port}"

    @property
    def neo4j_bolt_uri(self) -> str:
        """Neo4j Bolt URI for client connections."""
        return f"bolt://{self.service_public_host}:{self.neo4j_bolt_port}"

    @property
    def opensearch_admin_url(self) -> str:
        """OpenSearch Dashboards URL used by the dashboard."""
        return f"http://{self.service_public_host}:{self.opensearch_dashboards_port}"

    @property
    def opensearch_url(self) -> str:
        """OpenSearch HTTP endpoint for client connections."""
        return f"http://{self.service_public_host}:{self.opensearch_http_port}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
