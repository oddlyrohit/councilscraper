.PHONY: help install dev build run stop logs test lint format clean migrate scrape

# Default target
help:
	@echo "Council DA Scraper - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  dev         Start development environment"
	@echo ""
	@echo "Docker:"
	@echo "  build       Build Docker images"
	@echo "  run         Start all services"
	@echo "  stop        Stop all services"
	@echo "  logs        View logs"
	@echo "  clean       Remove containers and volumes"
	@echo ""
	@echo "Database:"
	@echo "  migrate     Run database migrations"
	@echo "  shell-db    Open PostgreSQL shell"
	@echo ""
	@echo "Scraping:"
	@echo "  scrape-tier1    Scrape all tier 1 councils"
	@echo "  scrape-tier2    Scrape all tier 2 councils"
	@echo "  scrape COUNCIL=xxx  Scrape specific council"
	@echo ""
	@echo "Testing:"
	@echo "  test        Run tests"
	@echo "  lint        Run linters"
	@echo "  format      Format code"

# =============================================================================
# Setup
# =============================================================================

install:
	pip install -e ".[dev]"
	playwright install chromium

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# =============================================================================
# Docker
# =============================================================================

build:
	docker-compose build

run:
	docker-compose up -d

run-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f worker

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# =============================================================================
# Database
# =============================================================================

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

shell-db:
	docker-compose exec db psql -U postgres -d council_da

# =============================================================================
# Scraping
# =============================================================================

scrape:
	docker-compose exec worker celery -A src.orchestrator.celery_app call src.orchestrator.tasks.scrape_council --args='["$(COUNCIL)", "active"]'

scrape-tier1:
	docker-compose exec worker celery -A src.orchestrator.celery_app call src.orchestrator.tasks.scrape_tier --args='[1, "active"]'

scrape-tier2:
	docker-compose exec worker celery -A src.orchestrator.celery_app call src.orchestrator.tasks.scrape_tier --args='[2, "active"]'

scrape-all:
	docker-compose exec worker celery -A src.orchestrator.celery_app call src.orchestrator.tasks.scrape_all_councils

backfill:
	docker-compose exec worker celery -A src.orchestrator.celery_app call src.orchestrator.tasks.backfill_council --args='["$(COUNCIL)", "$(START)", "$(END)"]'

# =============================================================================
# Testing
# =============================================================================

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# =============================================================================
# Monitoring
# =============================================================================

flower:
	open http://localhost:5555

grafana:
	open http://localhost:3000

api-docs:
	open http://localhost:8000/docs
