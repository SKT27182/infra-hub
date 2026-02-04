# 🏠 Infra Hub

**Centralized Infrastructure Management Platform**

A unified platform for managing shared infrastructure services on a single VM. Instead of running duplicate Docker containers for each project, deploy shared core services once and manage them all from one place.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Services & Ports](#-services--ports)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Admin UIs](#-admin-uis)
- [Configuration](#-configuration)

---

## ✨ Features

- **Centralized Docker Management** - Start, stop, restart containers from one dashboard
- **Service Health Monitoring** - Real-time health checks for all services
- **Deep Service Integration** - Browse databases, keys, collections, and buckets
- **Native Admin UI Access** - Quick links to pgAdmin, RedisInsight, Mongo Express, etc.
- **Modular Architecture** - Easily add new services without modifying core code
- **Auto-Refresh Dashboard** - Live updates every 5 seconds

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│                    http://localhost:3000                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│                    http://localhost:8000                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Docker Network                            │
│                       (infra-network)                           │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│  PostgreSQL │    Redis    │   MongoDB   │   Qdrant    │  MinIO  │
│   + pgAdmin │ + Insight   │ + Express   │             │+ Console│
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
```

---

## 🔌 Services & Ports

### Core Services

| Service | Container Name | Internal Port | External Port | Description |
|---------|----------------|---------------|---------------|-------------|
| **PostgreSQL** | `infra-postgres` | 5432 | **5432** | Primary relational database |
| **Redis** | `infra-redis` | 6379 | **6379** | In-memory cache & key-value store |
| **MongoDB** | `infra-mongodb` | 27017 | **27017** | Document database |
| **Qdrant** | `infra-qdrant` | 6333, 6334 | **6333**, **6334** | Vector database for AI/ML |
| **MinIO** | `infra-minio` | 9000, 9001 | **9000**, **9001** | S3-compatible object storage |

### Admin UIs

| Service | Container Name | Port | URL | Credentials |
|---------|----------------|------|-----|-------------|
| **pgAdmin** | `infra-pgadmin` | 5050 | http://localhost:5050 | See `.env` |
| **RedisInsight** | `infra-redisinsight` | 5540 | http://localhost:5540 | No auth |
| **Mongo Express** | `infra-mongo-express` | 8081 | http://localhost:8081 | See `.env` |
| **Qdrant Dashboard** | (built-in) | 6333 | http://localhost:6333/dashboard | No auth |
| **MinIO Console** | (built-in) | 9001 | http://localhost:9001 | See `.env` |

### Application

| Component | Port | URL | Description |
|-----------|------|-----|-------------|
| **Frontend** | 3000 | http://localhost:3000 | React dashboard |
| **Backend API** | 8000 | http://localhost:8000 | FastAPI REST API |
| **API Docs** | 8000 | http://localhost:8000/docs | Swagger UI |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ & pnpm
- uv (Python package manager)

### 1. Clone & Setup

```bash
cd /home/skt27182/Courses/Notes/Projects/infra-hub

# Copy environment template
cp .env.example .env

# Edit credentials (IMPORTANT!)
nano .env
```

### 2. Start Everything

```bash
# Start all services (Docker + Backend + Frontend)
make dev
```

Or start individually:

```bash
# Start Docker containers only
make up

# Start backend (in new terminal)
make dev-backend

# Start frontend (in new terminal)
make dev-frontend
```

### 3. Access Dashboard

Open http://localhost:3000

---

## 📁 Project Structure

```
infra-hub/
├── docker-compose.yml          # Docker service definitions
├── .env                        # Environment variables (credentials)
├── .env.example                # Template for .env
├── Makefile                    # Quick commands
├── README.md                   # This file
│
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── core/
│   │   │   ├── config.py       # Settings from .env
│   │   │   ├── docker.py       # Docker client wrapper
│   │   │   └── registry.py     # Service registry pattern
│   │   ├── services/           # Modular service handlers
│   │   │   ├── base.py         # BaseService abstract class
│   │   │   ├── postgres.py
│   │   │   ├── redis.py
│   │   │   ├── mongodb.py
│   │   │   ├── qdrant.py
│   │   │   └── minio.py
│   │   ├── api/
│   │   │   ├── deps.py         # Dependency injection
│   │   │   └── routes/
│   │   │       ├── health.py   # Health check endpoints
│   │   │       ├── containers.py
│   │   │       ├── services_api.py
│   │   │       └── services/   # Deep service routes
│   │   └── schemas/            # Pydantic models
│   ├── requirements.txt
│   └── .venv/                  # Virtual environment
│
├── frontend/                   # React + Vite Frontend
│   ├── src/
│   │   ├── App.tsx             # Main app with routes
│   │   ├── main.tsx            # Entry point
│   │   ├── index.css           # Tailwind + theme
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   ├── layout/         # Sidebar, AppLayout
│   │   │   └── services/       # ServiceCard
│   │   ├── pages/              # Route pages
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ServicesPage.tsx
│   │   │   ├── ContainersPage.tsx
│   │   │   ├── PostgresPage.tsx
│   │   │   ├── RedisPage.tsx
│   │   │   ├── MongoDBPage.tsx
│   │   │   ├── QdrantPage.tsx
│   │   │   └── MinIOPage.tsx
│   │   ├── hooks/              # React Query hooks
│   │   └── lib/
│   │       ├── api.ts          # API client
│   │       └── utils.ts        # Utilities
│   ├── package.json
│   └── vite.config.ts
│
└── services/                   # Service init scripts
    ├── postgres/init.sql
    └── mongodb/init-mongo.js
```

---

## 📡 API Reference

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |

### Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/services` | List all services with status |
| GET | `/api/services/{name}` | Get service details |
| GET | `/api/services/{name}/health` | Check service health |
| GET | `/api/services/{name}/info` | Get service metadata |
| POST | `/api/services/{name}/start` | Start service container |
| POST | `/api/services/{name}/stop` | Stop service container |
| POST | `/api/services/{name}/restart` | Restart service container |
| GET | `/api/services/{name}/logs` | Get container logs |

### Containers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/containers` | List all containers |
| GET | `/api/containers/infra` | List only infra containers |
| POST | `/api/containers/{id}/start` | Start container by ID |
| POST | `/api/containers/{id}/stop` | Stop container by ID |
| POST | `/api/containers/{id}/restart` | Restart container by ID |

### Deep Service Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/services/postgres/databases` | List PostgreSQL databases |
| GET | `/api/services/postgres/databases/{db}/tables` | List tables in database |
| GET | `/api/services/redis/keys` | List Redis keys (with pattern) |
| GET | `/api/services/redis/memory` | Redis memory stats |
| GET | `/api/services/mongodb/databases` | List MongoDB databases |
| GET | `/api/services/mongodb/databases/{db}/collections` | List collections |
| GET | `/api/services/qdrant/collections` | List Qdrant collections |
| GET | `/api/services/qdrant/collections/{name}` | Collection details |
| GET | `/api/services/minio/buckets` | List MinIO buckets |
| GET | `/api/services/minio/buckets/{name}` | Bucket details |

---

## 🛠️ Development

### Makefile Commands

```bash
make help           # Show all commands
make up             # Start all Docker services
make down           # Stop all Docker services
make restart        # Restart all services
make logs           # View logs (follow)
make ps             # Show running containers
make health         # Check service health
make clean          # Remove containers AND volumes (data loss!)
make dev            # Start everything (Docker + Backend + Frontend)
make dev-backend    # Start backend only
make dev-frontend   # Start frontend only
```

### Backend Development

```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
pnpm install
pnpm dev
```

### Adding a New Service

1. **Create service handler** in `backend/app/services/`:
```python
from app.services.base import BaseService

class NewService(BaseService):
    name = "newservice"
    display_name = "New Service"
    container_name = "infra-newservice"
    
    async def check_health(self) -> bool:
        # Implement health check
        pass
```

2. **Register in** `backend/app/main.py`:
```python
ServiceRegistry.register(NewService())
```

3. **Add to docker-compose.yml**

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# PostgreSQL
POSTGRES_USER=infra
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=infra_db

# pgAdmin
PGADMIN_EMAIL=admin@infra.local
PGADMIN_PASSWORD=your_secure_password

# MongoDB
MONGO_ROOT_USER=root
MONGO_ROOT_PASSWORD=your_secure_password

# Mongo Express
ME_BASIC_AUTH_USERNAME=admin
ME_BASIC_AUTH_PASSWORD=your_secure_password

# MinIO
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_secure_password

# Backend
CORS_ORIGINS=http://localhost:3000
```

### Docker Network

All services are connected via `infra-network`. Other projects can connect:

```yaml
# In your project's docker-compose.yml
networks:
  default:
    external: true
    name: infra-network
```

Then connect using service names:
- `postgres:5432`
- `redis:6379`
- `mongodb:27017`
- `qdrant:6333`
- `minio:9000`

---

## 📊 Resource Requirements

| Service | RAM (idle) | RAM (active) |
|---------|------------|--------------|
| PostgreSQL | ~50MB | 100-500MB |
| Redis | ~10MB | 50-200MB |
| MongoDB | ~100MB | 200-500MB |
| Qdrant | ~100MB | 200MB-1GB |
| MinIO | ~50MB | 100-300MB |
| pgAdmin | ~50MB | 100MB |
| RedisInsight | ~100MB | 150MB |
| Mongo Express | ~30MB | 50MB |
| **Total** | ~500MB | ~1-3GB |

Recommended VM: **8GB+ RAM** for comfortable operation with all services.

---

## 📄 License

MIT

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

Built with ❤️ for infrastructure simplicity
