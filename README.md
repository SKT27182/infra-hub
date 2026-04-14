# Infra Hub

Centralized infrastructure platform for running shared Docker services once and reusing them across projects.

## What this project does

- Runs core services in Docker (`postgres`, `redis`, `mongodb`, `qdrant`, `minio`) with persistent volumes
- Exposes service/admin status and control via FastAPI backend
- Provides a React dashboard frontend
- Keeps service URLs, container names, and ports environment-driven through `backend/config.py`
- Uses frontend `/api` calls with Vite dev proxy (local) and Nginx reverse proxy (server)

## Architecture

- **Frontend**: React + Vite (`frontend/`)
- **Backend**: FastAPI (`backend/`)
- **Infra**: Docker Compose (`docker-compose.yml`)

Frontend calls `'/api'` only:

- **Local dev**: Vite proxies `/api` to backend target from `VITE_DEV_API_TARGET`
- **Deployment**: Nginx proxies `/api` to backend service

## Environment files

- `backend/.env` - backend app port, CORS, service/admin host+ports, credentials
- `frontend/.env` - frontend dev port and local proxy target

Templates:

- `backend/.env.example`
- `frontend/.env.example`

## Quick start

### 1. Install dependencies

```bash
cd backend
uv venv .venv
uv sync

cd ../frontend
pnpm install
```

### 2. Start infrastructure containers

```bash
make up
```

### 3. Run backend and frontend

```bash
# terminal 1
make dev-backend

# terminal 2
make dev-frontend
```

Or run all together:

```bash
make dev
```

## Runtime URLs (env-driven)

Default local values are controlled by env:

- Frontend: `http://localhost:${VITE_PORT}`
- Backend API: `http://127.0.0.1:${API_PORT}`
- API docs: `http://127.0.0.1:${API_PORT}/docs`

Admin UI links in the dashboard are built from:

- `SERVICE_PUBLIC_HOST`
- service/admin port envs (for pgAdmin, RedisInsight, Mongo Express, Qdrant, MinIO)

## Important behavior

1. `make dev-backend` starts only backend, not Docker containers.
2. Start containers first with `make up` (or service-specific `make up-*`) before using login/docs/service APIs.
3. Docs/login auth needs PostgreSQL reachable.
4. Backend returns `503` when user DB is unavailable (instead of misleading `401` loops).

## Make commands

```bash
make up             # start all Docker services
make down           # stop Docker services
make stop           # stop Docker + local backend/frontend processes
make restart        # restart Docker services
make logs           # docker compose logs -f
make ps             # docker compose ps
make health         # quick health checks
make clean          # remove containers and volumes
make dev-backend    # run backend with backend/.env API_PORT
make dev-frontend   # run frontend with frontend/.env VITE_PORT
make dev            # start Docker + backend + frontend
```

## Reverse proxy note (Nginx)

Use one domain and proxy:

- `/` -> frontend
- `/api` -> backend

No frontend code changes are needed when moving from local to server because frontend uses relative `/api`.
