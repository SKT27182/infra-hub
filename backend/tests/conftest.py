"""Secure deterministic environment defaults for the backend test suite."""

import os

os.environ["ADMIN_PASSWORD"] = "test-admin-password-with-adequate-length"
os.environ["JWT_SECRET"] = "test-signing-secret-with-at-least-32-bytes"
os.environ["POSTGRES_PASSWORD"] = "test-postgres-password"
os.environ["PGADMIN_PASSWORD"] = "test-pgadmin-password"
os.environ["REDIS_PASSWORD"] = "test-redis-password"
os.environ["MONGO_PASSWORD"] = "test-mongodb-password"
os.environ["MINIO_PASSWORD"] = "test-minio-password"
os.environ["NEO4J_PASSWORD"] = "test-neo4j-password"
os.environ["QDRANT_API_KEY"] = "test-qdrant-api-key"
os.environ["API_HOST"] = "127.0.0.1"
os.environ["SERVICE_BIND_HOST"] = "127.0.0.1"
os.environ["BACKEND_LOG_FILE"] = "/private/tmp/infra-hub-backend-tests.log"
