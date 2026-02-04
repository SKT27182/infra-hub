# Infra Hub

Centralized Infrastructure Management Platform for a single VM.

## Quick Start

```bash
# Start all services
make up

# Check service health
make health

# View running containers
make ps

# View logs
make logs
```

## Services

| Service      | Port  | Admin UI              | Description                    |
| ------------ | ----- | --------------------- | ------------------------------ |
| PostgreSQL   | 5432  | pgAdmin (5050)        | Relational database            |
| Redis        | 6379  | RedisInsight (5540)   | Cache & pub/sub                |
| MongoDB      | 27017 | Mongo Express (8081)  | Document database              |
| Qdrant       | 6333  | Built-in (6333)       | Vector database                |
| MinIO        | 9000  | Console (9001)        | S3-compatible object storage   |

## Admin UIs

- **pgAdmin**: http://localhost:5050
- **RedisInsight**: http://localhost:5540
- **Mongo Express**: http://localhost:8081
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **MinIO Console**: http://localhost:9001

## Configuration

1. Copy `.env.example` to `.env`
2. Update passwords with secure values
3. Run `make up`

## Connecting from Other Projects

Projects can connect to these services via the `infra-network` Docker network or via localhost ports.

### Docker Network (Recommended)

Add this to your project's `docker-compose.yml`:

```yaml
networks:
  infra-network:
    external: true

services:
  your-app:
    networks:
      - infra-network
    environment:
      DATABASE_URL: postgresql://admin:password@infra-postgres:5432/your_db
      REDIS_URL: redis://:password@infra-redis:6379
      MONGO_URL: mongodb://admin:password@infra-mongodb:27017
      QDRANT_URL: http://infra-qdrant:6333
      MINIO_ENDPOINT: infra-minio:9000
```

### Localhost

For local development without Docker:

```
PostgreSQL: localhost:5432
Redis: localhost:6379
MongoDB: localhost:27017
Qdrant: localhost:6333
MinIO: localhost:9000
```

## Commands

```bash
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make logs            # View logs (follow mode)
make ps              # Show service status
make health          # Check service health
make clean           # Remove all containers and volumes (DESTRUCTIVE)

# Start specific services
make up-postgres     # PostgreSQL + pgAdmin
make up-redis        # Redis + RedisInsight
make up-mongodb      # MongoDB + Mongo Express
make up-qdrant       # Qdrant
make up-minio        # MinIO
```

## Project Structure

```
infra-hub/
├── docker-compose.yml      # Main compose file
├── .env.example            # Environment template
├── .env                    # Local secrets (gitignored)
├── Makefile                # Common commands
├── backend/                # FastAPI control plane (Phase 2)
├── frontend/               # Dashboard UI (Phase 3)
└── services/               # Service-specific configs
    ├── postgres/
    │   └── init.sql
    ├── mongodb/
    │   └── init-mongo.js
    ├── redis/
    ├── qdrant/
    └── minio/
```
