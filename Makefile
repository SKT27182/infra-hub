SHELL := /bin/bash

.PHONY: help install dev-local dev up down clean clean-all clean-hard print-urls prepare-logs stop-local wait-db logs ps health \
	up-postgres up-redis up-mongodb up-qdrant up-minio up-neo4j build

LOG_DIR := $(HOME)/.local/share/dev-logs/infra-hub
BACKEND_LOG := $(LOG_DIR)/backend.log
FRONTEND_LOG := $(LOG_DIR)/frontend.log
BACKEND_PID := $(LOG_DIR)/backend.pid
FRONTEND_PID := $(LOG_DIR)/frontend.pid
# DEV_LOG_MODE: file | console | both (default)
DEV_LOG_MODE ?= both
PERSIST_DIR := ./volumes
BACKEND_ENV_FILE := $(if $(wildcard backend/.env),backend/.env,backend/.env.example)
FRONTEND_ENV_FILE := $(if $(wildcard frontend/.env),frontend/.env,frontend/.env.example)
DOCKER_COMPOSE := docker compose --env-file $(BACKEND_ENV_FILE)
APP_HOST_RAW := $(shell awk -F= '/^SERVICE_PUBLIC_HOST=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
APP_HOST := $(if $(APP_HOST_RAW),$(APP_HOST_RAW),127.0.0.1)
BACKEND_PORT_RAW := $(shell awk -F= '/^API_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
BACKEND_PORT := $(if $(BACKEND_PORT_RAW),$(BACKEND_PORT_RAW),8888)
FRONTEND_PORT_RAW := $(shell awk -F= '/^VITE_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(FRONTEND_ENV_FILE) 2>/dev/null)
FRONTEND_PORT := $(if $(FRONTEND_PORT_RAW),$(FRONTEND_PORT_RAW),5143)
REDISINSIGHT_PORT_RAW := $(shell awk -F= '/^REDISINSIGHT_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
REDISINSIGHT_PORT := $(if $(REDISINSIGHT_PORT_RAW),$(REDISINSIGHT_PORT_RAW),5540)
MINIO_PORT_RAW := $(shell awk -F= '/^MINIO_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
MINIO_PORT := $(if $(MINIO_PORT_RAW),$(MINIO_PORT_RAW),9000)
MINIO_CONSOLE_PORT_RAW := $(shell awk -F= '/^MINIO_CONSOLE_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
MINIO_CONSOLE_PORT := $(if $(MINIO_CONSOLE_PORT_RAW),$(MINIO_CONSOLE_PORT_RAW),9001)
QDRANT_REST_PORT_RAW := $(shell awk -F= '/^QDRANT_REST_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
QDRANT_REST_PORT := $(if $(QDRANT_REST_PORT_RAW),$(QDRANT_REST_PORT_RAW),6333)
PGADMIN_PORT_RAW := $(shell awk -F= '/^PGADMIN_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
PGADMIN_PORT := $(if $(PGADMIN_PORT_RAW),$(PGADMIN_PORT_RAW),5050)
MONGO_EXPRESS_PORT_RAW := $(shell awk -F= '/^MONGO_EXPRESS_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
MONGO_EXPRESS_PORT := $(if $(MONGO_EXPRESS_PORT_RAW),$(MONGO_EXPRESS_PORT_RAW),8081)
REDIS_PASSWORD_RAW := $(shell awk -F= '/^REDIS_PASSWORD=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
REDIS_PASSWORD := $(if $(REDIS_PASSWORD_RAW),$(REDIS_PASSWORD_RAW),password)
QDRANT_API_KEY_RAW := $(shell awk -F= '/^QDRANT_API_KEY=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
NEO4J_HTTP_PORT_RAW := $(shell awk -F= '/^NEO4J_HTTP_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
NEO4J_HTTP_PORT := $(if $(NEO4J_HTTP_PORT_RAW),$(NEO4J_HTTP_PORT_RAW),7474)
NEO4J_BOLT_PORT_RAW := $(shell awk -F= '/^NEO4J_BOLT_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
NEO4J_BOLT_PORT := $(if $(NEO4J_BOLT_PORT_RAW),$(NEO4J_BOLT_PORT_RAW),7687)
INFRA_POSTGRES_CONTAINER ?= infra-postgres
CURL_MAX_TIME := 5

help:
	@echo "Infra Hub - Available commands"
	@echo ""
	@echo "  make install     - Install backend (uv sync) and frontend (pnpm install)"
	@echo "  make dev-local   - Start infra services in Docker + run backend/frontend locally"
	@echo "                     DEV_LOG_MODE=file|console|both (default: both)"
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
	@if [ "$(DEV_LOG_MODE)" != "console" ]; then \
		: > "$(BACKEND_LOG)"; \
		: > "$(FRONTEND_LOG)"; \
	fi

up:
	$(DOCKER_COMPOSE) up -d
	@$(MAKE) --no-print-directory print-urls

dev: up

dev-local: install prepare-logs up
	@$(MAKE) --no-print-directory stop-local
	@$(MAKE) --no-print-directory wait-db
	@echo "log mode: $(DEV_LOG_MODE)"
	@if [ "$(DEV_LOG_MODE)" != "console" ]; then \
		echo "backend log:  $(BACKEND_LOG)"; \
		echo "frontend log: $(FRONTEND_LOG)"; \
	fi
	@$(MAKE) --no-print-directory print-urls
	@bash -c 'set -euo pipefail; \
		log_mode="$(DEV_LOG_MODE)"; \
		case "$$log_mode" in file|console|both) ;; \
			*) echo "Invalid DEV_LOG_MODE: $$log_mode (use file, console, or both)" >&2; exit 1 ;; \
		esac; \
		setup_log_pipe() { \
			local logfile="$$1"; \
			case "$$log_mode" in \
				console) ;; \
				both) exec > >(tee -a "$$logfile") 2>&1 ;; \
				file|*) exec >> "$$logfile" 2>&1 ;; \
			esac; \
		}; \
		trap '"'"'kill $$backend_pid $$frontend_pid 2>/dev/null || true; rm -f "$(BACKEND_PID)" "$(FRONTEND_PID)"'"'"' INT TERM EXIT; \
		( setup_log_pipe "$(BACKEND_LOG)"; cd backend && set -a && [ -f .env ] && source .env; set +a; \
		  .venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port "$${API_PORT:-$(BACKEND_PORT)}" \
		) & backend_pid=$$!; echo $$backend_pid > "$(BACKEND_PID)"; \
		( setup_log_pipe "$(FRONTEND_LOG)"; cd frontend && pnpm dev ) & frontend_pid=$$!; echo $$frontend_pid > "$(FRONTEND_PID)"; \
		wait $$backend_pid $$frontend_pid'

stop-local:
	@if [ -f "$(BACKEND_PID)" ]; then kill "$$(cat "$(BACKEND_PID)")" 2>/dev/null || true; rm -f "$(BACKEND_PID)"; fi
	@if [ -f "$(FRONTEND_PID)" ]; then kill "$$(cat "$(FRONTEND_PID)")" 2>/dev/null || true; rm -f "$(FRONTEND_PID)"; fi
	@for port in "$(BACKEND_PORT)" "$(FRONTEND_PORT)"; do \
		pids="$$(ss -ltnp | awk -v p=":$$port$$" '$$4 ~ p {print}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"; \
		if [ -n "$$pids" ]; then \
			echo "Stopping processes on port $$port: $$pids"; \
			kill $$pids 2>/dev/null || true; \
		fi; \
	done

wait-db:
	@echo "Waiting for PostgreSQL container to be healthy..."
	@timeout 90 bash -c 'set -euo pipefail; \
		container="$(INFRA_POSTGRES_CONTAINER)"; \
		until docker inspect "$$container" >/dev/null 2>&1; do sleep 1; done; \
		while true; do \
			status=$$(docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" "$$container" 2>/dev/null || true); \
			if [ "$$status" = "healthy" ] || [ "$$status" = "running" ]; then \
				break; \
			fi; \
			sleep 1; \
		done'

down: stop-local
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

ps:
	$(DOCKER_COMPOSE) ps

health:
	@echo "=== Service Health Check ==="
	@echo ""
	@echo "PostgreSQL:"
	@docker exec infra-postgres pg_isready -U admin 2>/dev/null && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Redis:"
	@docker exec infra-redis redis-cli -a "$(REDIS_PASSWORD)" ping 2>/dev/null | grep -q PONG && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "MongoDB:"
	@docker exec infra-mongodb mongosh --quiet --eval "db.adminCommand('ping')" 2>/dev/null | grep -q 1 && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Qdrant:"
	@if [ -n "$(QDRANT_API_KEY_RAW)" ]; then \
		curl -sf --max-time $(CURL_MAX_TIME) -H "api-key: $(QDRANT_API_KEY_RAW)" "http://$(APP_HOST):$(QDRANT_REST_PORT)/readyz" | grep -q "ready" && echo "  ✓ Healthy" || echo "  ✗ Not ready"; \
	else \
		curl -sf --max-time $(CURL_MAX_TIME) "http://$(APP_HOST):$(QDRANT_REST_PORT)/health" | grep -q "ok" && echo "  ✓ Healthy" || echo "  ✗ Not ready"; \
	fi
	@echo ""
	@echo "MinIO API:"
	@curl -sf --max-time $(CURL_MAX_TIME) "http://$(APP_HOST):$(MINIO_PORT)/minio/health/live" >/dev/null && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Neo4j Browser:"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(NEO4J_HTTP_PORT)/" && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Admin UIs:"
	@curl -sf --max-time $(CURL_MAX_TIME) "http://$(APP_HOST):$(REDISINSIGHT_PORT)/api/health/" >/dev/null && echo "  ✓ RedisInsight ($(APP_HOST):$(REDISINSIGHT_PORT))" || echo "  ✗ RedisInsight not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(MINIO_CONSOLE_PORT)/" && echo "  ✓ MinIO Console ($(APP_HOST):$(MINIO_CONSOLE_PORT))" || echo "  ✗ MinIO Console not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(QDRANT_REST_PORT)/dashboard" && echo "  ✓ Qdrant dashboard ($(APP_HOST):$(QDRANT_REST_PORT)/dashboard)" || echo "  ✗ Qdrant dashboard not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(PGADMIN_PORT)/" && echo "  ✓ pgAdmin ($(APP_HOST):$(PGADMIN_PORT))" || echo "  ✗ pgAdmin not ready (container may still be starting)"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(MONGO_EXPRESS_PORT)/" && echo "  ✓ Mongo Express ($(APP_HOST):$(MONGO_EXPRESS_PORT))" || echo "  ✗ Mongo Express not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(NEO4J_HTTP_PORT)/" && echo "  ✓ Neo4j Browser ($(APP_HOST):$(NEO4J_HTTP_PORT))" || echo "  ✗ Neo4j Browser not ready"

build: install
	cd frontend && pnpm build

clean: stop-local
	rm -rf frontend/dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	rm -f "$(BACKEND_LOG)" "$(FRONTEND_LOG)"
	$(DOCKER_COMPOSE) down -v --remove-orphans

clean-hard: stop-local
	rm -f "$(BACKEND_LOG)" "$(FRONTEND_LOG)"
	$(DOCKER_COMPOSE) down --volumes --remove-orphans --rmi local
	rm -rf "$(PERSIST_DIR)"

print-urls:
	@echo "Backend URL:  http://$(APP_HOST):$(BACKEND_PORT)"
	@echo "Frontend URL: http://$(APP_HOST):$(FRONTEND_PORT)"
	@echo ""
	@echo "Admin UIs (from SERVICE_PUBLIC_HOST + port envs):"
	@echo "  pgAdmin:       http://$(APP_HOST):$(PGADMIN_PORT)"
	@echo "  RedisInsight:  http://$(APP_HOST):$(REDISINSIGHT_PORT)"
	@echo "  Mongo Express: http://$(APP_HOST):$(MONGO_EXPRESS_PORT)"
	@echo "  Qdrant:        http://$(APP_HOST):$(QDRANT_REST_PORT)/dashboard"
	@echo "  MinIO Console: http://$(APP_HOST):$(MINIO_CONSOLE_PORT)"
	@echo "  Neo4j Browser: http://$(APP_HOST):$(NEO4J_HTTP_PORT)"
	@echo "  Neo4j Bolt:    bolt://$(APP_HOST):$(NEO4J_BOLT_PORT)"

up-postgres:
	$(DOCKER_COMPOSE) up -d postgres pgadmin

up-redis:
	$(DOCKER_COMPOSE) up -d redis redisinsight

up-mongodb:
	$(DOCKER_COMPOSE) up -d mongodb mongo-express

up-qdrant:
	$(DOCKER_COMPOSE) up -d qdrant

up-minio:
	$(DOCKER_COMPOSE) up -d minio

up-neo4j:
	$(DOCKER_COMPOSE) up -d neo4j
