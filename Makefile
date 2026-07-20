SHELL := /bin/bash

# Local development must run as the invoking user so generated files, logs, and
# bind-mounted service data remain writable without elevated privileges.
ifneq ($(filter dev-local,$(MAKECMDGOALS)),)
ifneq ($(or $(SUDO_USER),$(filter 0,$(shell id -u))),)
$(error Do not run dev-local with sudo; run `make dev-local` as your normal user)
endif
endif

.PHONY: help install dev-local dev up down clean clean-all clean-hard print-urls prepare-logs stop-local wait-db db-bootstrap logs ps health \
	up-postgres up-redis up-mongodb up-qdrant up-minio up-neo4j up-opensearch build

LOG_DIR := $(HOME)/.local/share/projects/infra-hub/dev-logs
BACKEND_LOG := $(LOG_DIR)/backend.log
FRONTEND_LOG := $(LOG_DIR)/frontend.log
BACKEND_PID := $(LOG_DIR)/backend.pid
FRONTEND_PID := $(LOG_DIR)/frontend.pid
# DEV_LOG_MODE: file | console | both (default)
DEV_LOG_MODE ?= both
BACKEND_ENV_FILE := $(if $(wildcard backend/.env),backend/.env,backend/.env.example)
FRONTEND_ENV_FILE := $(if $(wildcard frontend/.env),frontend/.env,frontend/.env.example)
PERSIST_DIR_RAW := $(shell awk -F= '/^INFRA_PERSIST_DIR=/{value=$$2; gsub(/^[ \t]+|[ \t]+$$/,"",value); gsub(/\$$\{HOME\}/,ENVIRON["HOME"],value); gsub(/\$$HOME/,ENVIRON["HOME"],value); print value; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
PERSIST_DIR := $(if $(PERSIST_DIR_RAW),$(PERSIST_DIR_RAW),$(HOME)/.local/share/projects/infra-hub/volumes)
LOG_PATH_RAW := $(shell awk -F= '/^LOG_PATH=/{value=$$2; gsub(/^[ \t]+|[ \t]+$$/,"",value); gsub(/\$$\{HOME\}/,ENVIRON["HOME"],value); gsub(/\$$HOME/,ENVIRON["HOME"],value); print value; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
LOG_PATH := $(if $(LOG_PATH_RAW),$(LOG_PATH_RAW),$(LOG_DIR))
# Ensure compose interpolation always sees an absolute persist path.
export INFRA_PERSIST_DIR := $(PERSIST_DIR)
export LOG_PATH := $(LOG_PATH)
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
REDIS_PASSWORD := $(REDIS_PASSWORD_RAW)
POSTGRES_USER := $(shell awk -F= '/^POSTGRES_USER=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
POSTGRES_PASSWORD := $(shell awk -F= '/^POSTGRES_PASSWORD=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
POSTGRES_DB := $(shell awk -F= '/^POSTGRES_DB=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
QDRANT_API_KEY_RAW := $(shell awk -F= '/^QDRANT_API_KEY=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
NEO4J_HTTP_PORT_RAW := $(shell awk -F= '/^NEO4J_HTTP_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
NEO4J_HTTP_PORT := $(if $(NEO4J_HTTP_PORT_RAW),$(NEO4J_HTTP_PORT_RAW),7474)
NEO4J_BOLT_PORT_RAW := $(shell awk -F= '/^NEO4J_BOLT_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
NEO4J_BOLT_PORT := $(if $(NEO4J_BOLT_PORT_RAW),$(NEO4J_BOLT_PORT_RAW),7687)
OPENSEARCH_HTTP_PORT_RAW := $(shell awk -F= '/^OPENSEARCH_HTTP_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
OPENSEARCH_HTTP_PORT := $(if $(OPENSEARCH_HTTP_PORT_RAW),$(OPENSEARCH_HTTP_PORT_RAW),9200)
OPENSEARCH_DASHBOARDS_PORT_RAW := $(shell awk -F= '/^OPENSEARCH_DASHBOARDS_PORT=/{gsub(/^[ \t]+|[ \t]+$$/,"",$$2); print $$2; exit}' $(BACKEND_ENV_FILE) 2>/dev/null)
OPENSEARCH_DASHBOARDS_PORT := $(if $(OPENSEARCH_DASHBOARDS_PORT_RAW),$(OPENSEARCH_DASHBOARDS_PORT_RAW),5601)
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
	@echo "  make clean-all   - Clean infra-hub logs + Docker volumes"
	@echo "  make clean-hard  - Force clean infra-hub shared services (containers, volumes, images, logs)"
	@echo "                     Data dir: $(PERSIST_DIR)"
	@echo "                     Use this only when you intend to tear down Redis/MinIO/Postgres/etc."
	@echo "  make wait-db      - wait for infra-postgres healthy + credentials work"
	@echo "  make db-bootstrap - ensure users table + default admin (used by dev-local)"
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
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d
	@$(MAKE) --no-print-directory print-urls

dev: up

dev-local: install prepare-logs up
	@$(MAKE) --no-print-directory stop-local
	@$(MAKE) --no-print-directory wait-db
	@$(MAKE) --no-print-directory db-bootstrap
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
		( setup_log_pipe "$(BACKEND_LOG)"; cd backend && \
		  .venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port "$(BACKEND_PORT)" \
		) & backend_pid=$$!; echo $$backend_pid > "$(BACKEND_PID)"; \
		( setup_log_pipe "$(FRONTEND_LOG)"; cd frontend && pnpm dev ) & frontend_pid=$$!; echo $$frontend_pid > "$(FRONTEND_PID)"; \
		wait $$backend_pid $$frontend_pid'

stop-local:
	@if [ -f "$(BACKEND_PID)" ]; then kill "$$(cat "$(BACKEND_PID)")" 2>/dev/null || true; rm -f "$(BACKEND_PID)"; fi
	@if [ -f "$(FRONTEND_PID)" ]; then kill "$$(cat "$(FRONTEND_PID)")" 2>/dev/null || true; rm -f "$(FRONTEND_PID)"; fi
	@# lsof is available on macOS and many Linux systems; ss covers minimal Linux hosts.
	@for port in "$(BACKEND_PORT)" "$(FRONTEND_PORT)"; do \
		if command -v lsof >/dev/null 2>&1; then \
			pids="$$(lsof -nP -tiTCP:"$$port" -sTCP:LISTEN 2>/dev/null || true)"; \
		elif command -v ss >/dev/null 2>&1; then \
			pids="$$(ss -ltnp | awk -v p=":$$port$$" '$$4 ~ p {print}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"; \
		else \
			echo "WARNING: cannot inspect port $$port (install lsof or ss)" >&2; \
			pids=""; \
		fi; \
		if [ -n "$$pids" ]; then \
			echo "Stopping processes on port $$port: $$pids"; \
			kill $$pids 2>/dev/null || true; \
		fi; \
	done

wait-db:
	@echo "Waiting for PostgreSQL container to be healthy..."
	@# Bash's SECONDS provides a timeout without GNU coreutils (Linux) or gtimeout (macOS).
	@bash -c 'set -euo pipefail; \
		container="$(INFRA_POSTGRES_CONTAINER)"; \
		deadline=$$((SECONDS + 90)); \
		while (( SECONDS < deadline )); do \
			status=$$(docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" "$$container" 2>/dev/null || true); \
			if [ "$$status" = "healthy" ] || [ "$$status" = "running" ]; then \
				exit 0; \
			fi; \
			sleep 1; \
		done; \
		echo "ERROR: PostgreSQL container did not become ready within 90 seconds." >&2; \
		exit 1'
	@echo "Verifying PostgreSQL credentials from backend/.env..."
	@if [ -z "$(POSTGRES_USER)" ] || [ -z "$(POSTGRES_PASSWORD)" ] || [ -z "$(POSTGRES_DB)" ]; then \
		echo "ERROR: POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB must be set in $(BACKEND_ENV_FILE)" >&2; \
		exit 1; \
	fi
	@bash -c 'set -euo pipefail; \
		deadline=$$((SECONDS + 60)); \
		while (( SECONDS < deadline )); do \
			if docker exec -e PGPASSWORD="$(POSTGRES_PASSWORD)" "$(INFRA_POSTGRES_CONTAINER)" \
				psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)" -tAc "SELECT 1" >/dev/null 2>&1; then \
				exit 0; \
			fi; \
			sleep 1; \
		done; \
		exit 1' || ( \
		echo "ERROR: cannot authenticate to Postgres with POSTGRES_* from $(BACKEND_ENV_FILE)." >&2; \
		echo "If you changed the password after the volume was created, reset infra data:" >&2; \
		echo "  make clean-hard && make up" >&2; \
		exit 1; \
	)
	@echo "PostgreSQL is ready."

db-bootstrap: ## Ensure users table and default admin exist
	@echo "Bootstrapping Infra Hub user store..."
	cd backend && .venv/bin/python -m scripts.db_bootstrap

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
	@echo "OpenSearch:"
	@curl -sf --max-time $(CURL_MAX_TIME) "http://$(APP_HOST):$(OPENSEARCH_HTTP_PORT)/_cluster/health" >/dev/null && echo "  ✓ Healthy" || echo "  ✗ Not ready"
	@echo ""
	@echo "Admin UIs:"
	@curl -sf --max-time $(CURL_MAX_TIME) "http://$(APP_HOST):$(REDISINSIGHT_PORT)/api/health/" >/dev/null && echo "  ✓ RedisInsight ($(APP_HOST):$(REDISINSIGHT_PORT))" || echo "  ✗ RedisInsight not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(MINIO_CONSOLE_PORT)/" && echo "  ✓ MinIO Console ($(APP_HOST):$(MINIO_CONSOLE_PORT))" || echo "  ✗ MinIO Console not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(QDRANT_REST_PORT)/dashboard" && echo "  ✓ Qdrant dashboard ($(APP_HOST):$(QDRANT_REST_PORT)/dashboard)" || echo "  ✗ Qdrant dashboard not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(PGADMIN_PORT)/" && echo "  ✓ pgAdmin ($(APP_HOST):$(PGADMIN_PORT))" || echo "  ✗ pgAdmin not ready (container may still be starting)"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(MONGO_EXPRESS_PORT)/" && echo "  ✓ Mongo Express ($(APP_HOST):$(MONGO_EXPRESS_PORT))" || echo "  ✗ Mongo Express not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) -o /dev/null "http://$(APP_HOST):$(NEO4J_HTTP_PORT)/" && echo "  ✓ Neo4j Browser ($(APP_HOST):$(NEO4J_HTTP_PORT))" || echo "  ✗ Neo4j Browser not ready"
	@curl -sf --max-time $(CURL_MAX_TIME) "http://$(APP_HOST):$(OPENSEARCH_DASHBOARDS_PORT)/api/status" >/dev/null && echo "  ✓ OpenSearch Dashboards ($(APP_HOST):$(OPENSEARCH_DASHBOARDS_PORT))" || echo "  ✗ OpenSearch Dashboards not ready"

build: install
	cd frontend && pnpm build

clean: stop-local
	rm -rf frontend/dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	rm -rf "$(LOG_DIR)"
	$(DOCKER_COMPOSE) down -v --remove-orphans

# Tears down shared infra (Redis, MinIO, Postgres, …). Other apps may depend on these.
clean-hard: stop-local
	rm -rf "$(LOG_DIR)"
	$(DOCKER_COMPOSE) down --volumes --remove-orphans --rmi local
	rm -rf "$(PERSIST_DIR)"

print-urls:
	@echo "Backend URL:  http://$(APP_HOST):$(BACKEND_PORT)"
	@echo "Frontend URL: http://$(APP_HOST):$(FRONTEND_PORT)"
	@echo "Data dir:     $(HOME)/.local/share/projects/infra-hub"
	@echo "Persist dir:  $(PERSIST_DIR)"
	@echo "Logs dir:     $(LOG_DIR)"
	@echo ""
	@echo "Admin UIs (from SERVICE_PUBLIC_HOST + port envs):"
	@echo "  pgAdmin:       http://$(APP_HOST):$(PGADMIN_PORT)"
	@echo "  RedisInsight:  http://$(APP_HOST):$(REDISINSIGHT_PORT)"
	@echo "  Mongo Express: http://$(APP_HOST):$(MONGO_EXPRESS_PORT)"
	@echo "  Qdrant:        http://$(APP_HOST):$(QDRANT_REST_PORT)/dashboard"
	@echo "  MinIO Console: http://$(APP_HOST):$(MINIO_CONSOLE_PORT)"
	@echo "  Neo4j Browser: http://$(APP_HOST):$(NEO4J_HTTP_PORT)"
	@echo "  Neo4j Bolt:    bolt://$(APP_HOST):$(NEO4J_BOLT_PORT)"
	@echo "  OpenSearch:    http://$(APP_HOST):$(OPENSEARCH_HTTP_PORT)"
	@echo "  OS Dashboards: http://$(APP_HOST):$(OPENSEARCH_DASHBOARDS_PORT)"

up-postgres:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d postgres pgadmin

up-redis:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d redis redisinsight

up-mongodb:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d mongodb mongo-express

up-qdrant:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d qdrant

up-minio:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d minio

up-neo4j:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d neo4j

up-opensearch:
	@mkdir -p "$(PERSIST_DIR)"
	$(DOCKER_COMPOSE) up -d opensearch opensearch-dashboards
