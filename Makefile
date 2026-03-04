.PHONY: help up down build logs restart clean test lint format migrate seed

# ─── Default ────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Docker ─────────────────────────────────────────────────
up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Rebuild all images
	docker compose build --no-cache

restart: ## Restart all services
	docker compose restart

logs: ## Tail all logs
	docker compose logs -f --tail=100

logs-api: ## Tail API logs
	docker compose logs -f --tail=100 api

logs-worker: ## Tail worker logs
	docker compose logs -f --tail=100 worker

logs-web: ## Tail frontend logs
	docker compose logs -f --tail=100 web

ps: ## Show running containers
	docker compose ps

# ─── Development ────────────────────────────────────────────
dev-api: ## Run API locally (hot reload)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Run frontend locally (hot reload)
	cd frontend && npm run dev

dev-worker: ## Run Celery worker locally
	cd backend && celery -A app.worker.celery_app worker --loglevel=info -Q analysis

dev-beat: ## Run Celery beat locally
	cd backend && celery -A app.worker.celery_app beat --loglevel=info

# ─── Testing ────────────────────────────────────────────────
test: ## Run all backend tests
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

test-fast: ## Run tests without coverage
	cd backend && pytest tests/ -v -x

test-watch: ## Run tests in watch mode
	cd backend && pytest-watch -- tests/ -v

# ─── Linting & Formatting ──────────────────────────────────
lint: ## Lint backend and frontend
	cd backend && ruff check app/
	cd frontend && npx next lint

format: ## Format backend code
	cd backend && ruff format app/
	cd backend && ruff check --fix app/

typecheck: ## Type check all code
	cd backend && mypy app/ --ignore-missing-imports
	cd frontend && npx tsc --noEmit

# ─── Database ──────────────────────────────────────────────
migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new MSG="add column")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U threatscan -d threatscan

db-reset: ## Reset database (destroy + recreate)
	docker compose down -v
	docker compose up -d postgres
	sleep 3
	docker compose up -d

# ─── Utilities ──────────────────────────────────────────────
seed: ## Seed database with sample data
	cd backend && python -m scripts.seed_data

shell: ## Open Python shell with app context
	cd backend && python -c "from app.database import *; from app.models import *; print('Models loaded.')"

clean: ## Remove all containers, volumes, and build artifacts
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.mypy_cache frontend/.next frontend/node_modules

yara-check: ## Validate all YARA rules
	python -c "import yara, glob; [print(f'  ✓ {p}') or yara.compile(filepath=p) for p in glob.glob('yara-rules/*.yar')]"

# ─── Production ────────────────────────────────────────────
prod-up: ## Start in production mode
	docker compose -f docker-compose.yml up -d --build

prod-down: ## Stop production
	docker compose -f docker-compose.yml down
