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
make install
```

### 2. Start full local development (infra in Docker + apps locally)

```bash
make dev-local
```

Logs are written to `~/.local/share/dev-logs/infra-hub/`:

```bash
tail -f ~/.local/share/dev-logs/infra-hub/backend.log ~/.local/share/dev-logs/infra-hub/frontend.log
```

### 3. Run infra services in Docker only

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

1. `make dev` runs infra services in Docker only.
2. `make dev-local` starts Docker infra services, then runs backend/frontend locally.
3. Docs/login auth needs PostgreSQL reachable.
4. Backend returns `503` when user DB is unavailable (instead of misleading `401` loops).

## Make commands

```bash
make up             # start all Docker services
make down           # stop Docker services + local backend/frontend pids
make dev            # run infra services in Docker
make dev-local      # run infra (Docker) + backend/frontend locally
make logs           # docker compose logs -f
make ps             # docker compose ps
make health         # quick health checks
make clean          # remove local caches and pid files
make clean-all      # remove logs + Docker volumes
```

## Reverse proxy note (Nginx)

Use one domain and proxy:

- `/` -> frontend
- `/api` -> backend

No frontend code changes are needed when moving from local to server because frontend uses relative `/api`.
