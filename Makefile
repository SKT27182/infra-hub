SHELL := /bin/bash

.PHONY: help install dev-local dev up down clean clean-all clean-hard print-urls prepare-logs stop-local logs ps health \
	up-postgres up-redis up-mongodb up-qdrant up-minio build

LOG_DIR := $(HOME)/.local/share/dev-logs/infra-hub
BACKEND_LOG := $(LOG_DIR)/backend.log
FRONTEND_LOG := $(LOG_DIR)/frontend.log
BACKEND_PID := $(LOG_DIR)/backend.pid
FRONTEND_PID := $(LOG_DIR)/frontend.pid
BACKEND_ENV_FILE := $(if $(wildcard backend/.env),backend/.env,backend/.env.example)
FRONTEND_ENV_FILE := $(if $(wildcard frontend/.env),frontend/.env,frontend/.env.example)
APP_HOST_RAW := $(shell awk -F= '/^SERVICE_PUBLIC_HOST=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
APP_HOST := $(if $(APP_HOST_RAW),$(APP_HOST_RAW),127.0.0.1)
BACKEND_PORT_RAW := $(shell awk -F= '/^API_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
BACKEND_PORT := $(if $(BACKEND_PORT_RAW),$(BACKEND_PORT_RAW),8888)
FRONTEND_PORT_RAW := $(shell awk -F= '/^VITE_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(FRONTEND_ENV_FILE) 2>/dev/null)
FRONTEND_PORT := $(if $(FRONTEND_PORT_RAW),$(FRONTEND_PORT_RAW),5143)

help:
	@echo "Infra Hub - Available commands"
	@echo ""
	@echo "  make install     - Install backend (uv sync) and frontend (pnpm install)"
	@echo "  make dev-local   - Start infra services in Docker + run backend/frontend locally"
	@echo "  make dev         - Run infra services in Docker"
	@echo "  make down        - Stop Docker services and local backend/frontend processes"
	@echo "  make clean       - Remove local caches and pid files"
	@echo "  make clean-all   - Clean everything (logs + Docker volumes)"
	@echo "  make clean-hard  - Force clean (containers, volumes, images, logs)"
	@echo "  make print-urls  - Show backend/frontend URLs from env ports"
	@echo ""
	@echo "Useful extras:"
	@echo "  make logs        - docker compose logs -f"
	@echo "  make ps          - docker compose ps"
	@echo "  make health      - quick health checks"

install:
	cd backend && uv sync
	cd frontend && pnpm install

prepare-logs:
	@mkdir -p "$(LOG_DIR)"
	@: > "$(BACKEND_LOG)"
	@: > "$(FRONTEND_LOG)"

up:
	docker compose up -d
	@$(MAKE) --no-print-directory print-urls

dev: up

dev-local: install prepare-logs up
	@echo "backend log:  $(BACKEND_LOG)"
	@echo "frontend log: $(FRONTEND_LOG)"
	@$(MAKE) --no-print-directory print-urls
	@bash -c 'set -euo pipefail; \
		trap '"'"'kill $$backend_pid $$frontend_pid 2>/dev/null || true; rm -f "$(BACKEND_PID)" "$(FRONTEND_PID)"'"'"' INT TERM EXIT; \
		( cd backend && set -a && [ -f .env ] && source .env; set +a; \
		  .venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port "$${API_PORT:-$(BACKEND_PORT)}" \
		) >> "$(BACKEND_LOG)" 2>&1 & backend_pid=$$!; echo $$backend_pid > "$(BACKEND_PID)"; \
		( cd frontend && pnpm dev ) >> "$(FRONTEND_LOG)" 2>&1 & frontend_pid=$$!; echo $$frontend_pid > "$(FRONTEND_PID)"; \
		wait $$backend_pid $$frontend_pid'

stop-local:
	@if [ -f "$(BACKEND_PID)" ]; then kill "$$(cat "$(BACKEND_PID)")" 2>/dev/null || true; rm -f "$(BACKEND_PID)"; fi
	@if [ -f "$(FRONTEND_PID)" ]; then kill "$$(cat "$(FRONTEND_PID)")" 2>/dev/null || true; rm -f "$(FRONTEND_PID)"; fi

down: stop-local
	docker compose down

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
	@curl -s http://localhost:9000/minio/health/live >/dev/null && echo "  ✓ Healthy" || echo "  ✗ Not ready"

build: install
	cd frontend && pnpm build

clean: stop-local
	rm -rf frontend/dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	rm -f "$(BACKEND_LOG)" "$(FRONTEND_LOG)"
	docker compose down -v --remove-orphans

clean-hard: stop-local
	rm -f "$(BACKEND_LOG)" "$(FRONTEND_LOG)"
	docker compose down --volumes --remove-orphans --rmi local

print-urls:
	@echo "Backend URL:  http://$(APP_HOST):$(BACKEND_PORT)"
	@echo "Frontend URL: http://$(APP_HOST):$(FRONTEND_PORT)"

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
