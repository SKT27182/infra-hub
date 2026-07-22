# Infra Hub Backend

FastAPI backend for service orchestration, auth, status checks, and service info APIs.

For the full service guide (what each infra service does, admin UIs, credentials, troubleshooting, and Make commands), see the [repository README](../README.md).

## Environment configuration

Use `backend/.env` (template: `backend/.env.example`).

Key variables:

- `API_HOST` / `API_PORT`: loopback bind address and backend port
- `HOST_ONLY_MODE`: rejects wildcard API/service binds when true
- `CORS_ORIGINS`: allowed origins (comma-separated or JSON array)
- `SERVICE_PUBLIC_HOST`: host used to build admin URLs returned to frontend
- `ADMIN_EMAIL`: default admin login email (seeded at startup)
- `ADMIN_PASSWORD`: default admin login password (seeded at startup)

All service metadata (service names, display names, container names, admin URLs) is read from `config.py` and sourced from env.

## Local run (uv)

Infra Hub v2 requires Python 3.12 or newer.

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
- Swagger UI: `http://127.0.0.1:${API_PORT}/api/v2/docs`
- OpenAPI JSON: `http://127.0.0.1:${API_PORT}/api/v2/openapi.json`
- Application APIs: `http://127.0.0.1:${API_PORT}/api/v2/*`

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
| Neo4j Browser | `infra-neo4j` | `7474` | `NEO4J_HTTP_PORT` | `7474` | `http://<SERVICE_PUBLIC_HOST>:<NEO4J_HTTP_PORT>` |
| Neo4j Bolt | `infra-neo4j` | `7687` | `NEO4J_BOLT_PORT` | `7687` | `bolt://<SERVICE_PUBLIC_HOST>:<NEO4J_BOLT_PORT>` |
| OpenSearch | `infra-opensearch` | `9200` | `OPENSEARCH_HTTP_PORT` | `9200` | `http://<SERVICE_PUBLIC_HOST>:<OPENSEARCH_HTTP_PORT>` |
| OpenSearch Dashboards | `infra-opensearch-dashboards` | `5601` | `OPENSEARCH_DASHBOARDS_PORT` | `5601` | `http://<SERVICE_PUBLIC_HOST>:<OPENSEARCH_DASHBOARDS_PORT>` |

## Admin access API

Each service status includes `admin_url` and an optional `admin` runtime object.
The object is present for pgAdmin, RedisInsight, Mongo Express, and OpenSearch
Dashboards and contains `container_name`, `running`, `healthy`, and `status`.
Embedded admin interfaces return `admin: null`.

Authenticated admin-container actions are available at:

- `POST /api/v2/services/{name}/admin/start`
- `POST /api/v2/services/{name}/admin/stop`

Starting an admin container requires its primary service to be running. These
endpoints affect only the admin container; the existing service actions remain
grouped. Each service `get_info()` response may also include an `admin_access`
block with URL, instructions, optional login metadata, and Qdrant API-key hints.

## Notes

- Backend docs/login auth depends on PostgreSQL user lookup.
- On startup, the v2 user table is created when absent and the default admin is inserted only when absent. Existing rows are never updated or reactivated.
- If user DB is unreachable, auth/docs return `503` (not `401`) to avoid browser auth retry loops.
- If using a reverse proxy, expose only `/api/v2` and preserve same-origin cookie semantics.
- See [the v2 upgrade guide](../docs/V2_UPGRADE.md) for fresh deployment, account provisioning, and rollout checks.
