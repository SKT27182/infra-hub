# Infra Hub Backend

FastAPI backend for service orchestration, auth, status checks, and service info APIs.

## Environment configuration

Use `backend/.env` (template: `backend/.env.example`).

Key variables:

- `API_PORT`: backend bind port
- `CORS_ORIGINS`: allowed origins (comma-separated or JSON array)
- `SERVICE_PUBLIC_HOST`: host used to build admin URLs returned to frontend

All service metadata (service names, display names, container names, admin URLs) is read from `config.py` and sourced from env.

## Local run (uv)

```bash
cd backend
uv sync
uv run python main.py
```

or from repository root:

```bash
make dev-backend
```

## API entrypoints

- Root: `http://127.0.0.1:${API_PORT}/`
- Swagger UI: `http://127.0.0.1:${API_PORT}/docs`
- OpenAPI JSON: `http://127.0.0.1:${API_PORT}/openapi.json`
- Application APIs: `http://127.0.0.1:${API_PORT}/api/*`

## Service ports and access (env-driven)

| Service | Container | Internal Port(s) | Host Port Env | Default Host Port | Access |
|---|---|---|---|---|---|
| PostgreSQL | `infra-postgres` | `5432` | `POSTGRES_PORT` | `54321` | `postgresql://<user>:<password>@<host>:<port>/<db>` |
| pgAdmin | `infra-pgadmin` | `80` | `PGADMIN_PORT` | `5050` | `http://<SERVICE_PUBLIC_HOST>:<PGADMIN_PORT>` |
| Redis | `infra-redis` | `6379` | `REDIS_PORT` | `63791` | `redis://:<password>@<host>:<port>` |
| RedisInsight | `infra-redisinsight` | `5540` | `REDISINSIGHT_PORT` | `5540` | `http://<SERVICE_PUBLIC_HOST>:<REDISINSIGHT_PORT>` |
| MongoDB | `infra-mongodb` | `27017` | `MONGODB_PORT` | `27018` | `mongodb://<user>:<password>@<host>:<port>` |
| Mongo Express | `infra-mongo-express` | `8081` | `MONGO_EXPRESS_PORT` | `8081` | `http://<SERVICE_PUBLIC_HOST>:<MONGO_EXPRESS_PORT>` |
| Qdrant REST | `infra-qdrant` | `6333` | `QDRANT_REST_PORT` | `6333` | `http://<SERVICE_PUBLIC_HOST>:<QDRANT_REST_PORT>` |
| Qdrant gRPC | `infra-qdrant` | `6334` | `QDRANT_GRPC_PORT` | `6334` | gRPC endpoint |
| MinIO API | `infra-minio` | `9000` | `MINIO_PORT` | `9000` | `http://<SERVICE_PUBLIC_HOST>:<MINIO_PORT>` |
| MinIO Console | `infra-minio` | `9001` | `MINIO_CONSOLE_PORT` | `9001` | `http://<SERVICE_PUBLIC_HOST>:<MINIO_CONSOLE_PORT>` |

## Notes

- Backend docs/login auth depends on PostgreSQL user lookup.
- If user DB is unreachable, auth/docs return `503` (not `401`) to avoid browser auth retry loops.
- In production, use Nginx reverse proxy for `/api` to backend.
