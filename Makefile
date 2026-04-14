.PHONY: help up down restart logs ps health clean

# Default target
help:
	@echo "Infra Hub - Centralized Infrastructure Management"
	@echo ""
	@echo "Usage:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop docker services"
	@echo "  make stop      - Stop all (Docker + Apps)"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - View logs (follow mode)"
	@echo "  make ps        - Show service status"
	@echo "  make health    - Check service health"
	@echo "  make clean     - Remove all containers and volumes (DESTRUCTIVE)"
	@echo ""
	@echo "Service-specific:"
	@echo "  make up-postgres    - Start PostgreSQL only"
	@echo "  make up-redis       - Start Redis only"
	@echo "  make up-mongodb     - Start MongoDB only"
	@echo "  make up-qdrant      - Start Qdrant only"
	@echo "  make up-minio       - Start MinIO only"
	@echo ""
	@echo "Admin UIs:"
	@echo "  pgAdmin:       http://localhost:5050"
	@echo "  RedisInsight:  http://localhost:5540"
	@echo "  Mongo Express: http://localhost:8081"
	@echo "  Qdrant:        http://localhost:6333/dashboard"
	@echo "  MinIO Console: http://localhost:9001"

# =============================================================================
# Main Commands
# =============================================================================
up:
	docker compose up -d

down:
	docker compose down

stop:
	@echo "Stopping Docker services..."
	@docker compose down
	@echo "Stopping backend and frontend processes..."
	@-pkill -f "uvicorn main:app" || true
	@-pkill -f "vite" || true
	@echo "All services stopped."

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

health:
	@echo "=== Service Health Check ==="
	@echo ""
	@echo "PostgreSQL:"
	@docker exec infra-postgres pg_isready -U admin 2>/dev/null && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Redis:"
	@docker exec infra-redis redis-cli -a admin ping 2>/dev/null | grep -q PONG && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "MongoDB:"
	@docker exec infra-mongodb mongosh --quiet --eval "db.adminCommand('ping')" 2>/dev/null | grep -q 1 && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Qdrant:"
	@curl -s http://localhost:6333/health | grep -q "ok" && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "MinIO:"
	@curl -s http://localhost:9000/minio/health/live && echo "  ✓ Healthy" || echo "  ✗ Not ready"

clean:
	@echo "WARNING: This will remove all containers and volumes!"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] && \
		docker compose down -v --remove-orphans || echo "Cancelled"

# =============================================================================
# Service-Specific Commands
# =============================================================================
up-postgres:
	docker compose up -d postgres pgadmin

up-redis:
	docker compose up -d redis redisinsight

up-mongodb:
	docker compose up -d mongodb mongo-express

up-qdrant:
	docker compose up -d qdrant

up-minio:
	docker compose up -d minio

# =============================================================================
# Development
# =============================================================================
dev-backend:
	cd backend && set -a && . ./.env && set +a && .venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port "$$API_PORT"

dev-frontend:
	cd frontend && pnpm dev

dev:
	@echo "Starting all services..."
	@make up
	@echo "Waiting for Docker services to start..."
	@sleep 5
	@echo "Starting backend and frontend..."
	@trap 'kill 0' SIGINT; \
		(cd backend && set -a && . ./.env && set +a && .venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port "$$API_PORT") & \
		(cd frontend && pnpm dev) & \
		wait
