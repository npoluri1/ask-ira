# =============================================================================
# Ask IRA — Makefile
# =============================================================================
# Quick commands for local dev, test, build, and deploy.
# Usage: make <command>
# =============================================================================

.PHONY: help install lint format typecheck test audit docker-build docker-up \
        docker-down docker-dev docker-monitor seed k8s-deploy k8s-rollback \
        k8s-logs vercel-deploy render-deploy precommit all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (core + OpenAI + dev)
	pip install -e ".[dev,mcp,eval]"

lint: ## Run ruff linter
	ruff check src/ tests/ scripts/ --fix

format: ## Format code with ruff
	ruff format src/ tests/ scripts/

typecheck: ## Run mypy type checker
	mypy src/ --ignore-missing-imports --warn-unused-ignores || true

test: ## Run unit tests (skips slow integration tests that call real LLMs)
	pytest tests/ -v -m "not slow" --cov=src --cov-report=term --cov-report=html --timeout=60

test-all: ## Run all tests including slow integration tests
	pytest tests/ -v -m "slow" --timeout=180

audit: ## Audit dependencies for vulnerabilities
	pip-audit --strict --progress-spinner=off

# --- Docker ---
docker-build: ## Build production Docker image
	docker build -f deployment/Dockerfile -t ask-ira:latest .

docker-up: ## Start full stack with Docker Compose
	docker compose -f deployment/docker-compose.yml up --build -d

docker-down: ## Stop Docker Compose stack
	docker compose -f deployment/docker-compose.yml down

docker-dev: ## Start dev stack with hot-reload
	docker compose -f deployment/docker-compose.yml \
		-f deployment/docker-compose.override.yml up --build -d

docker-monitor: ## Start monitoring stack (Prometheus + Grafana)
	docker compose -f deployment/docker-compose.yml \
		-f deployment/docker-compose.monitoring.yml \
		--profile monitoring up --build -d

seed: ## Seed database with sample data
	docker compose -f deployment/docker-compose.yml \
		--profile seed run --rm seed

# --- Kubernetes ---
k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f deployment/kubernetes/configmap.yaml
	kubectl apply -f deployment/kubernetes/secrets.yaml
	kubectl apply -f deployment/kubernetes/deployment.yaml
	kubectl apply -f deployment/kubernetes/hpa.yaml
	kubectl apply -f deployment/kubernetes/ingress.yaml
	kubectl rollout status deployment/ask-ira --timeout=120s

k8s-rollback: ## Rollback Kubernetes deployment
	kubectl rollout undo deployment/ask-ira

k8s-logs: ## Tail K8s pod logs
	kubectl logs -f deployment/ask-ira

# --- Cloud Deploy ---
vercel-deploy: ## Deploy to Vercel (free tier, REST only)
	vercel deploy --prod --yes

render-deploy: ## Deploy to Render (free tier)
	@echo "Triggering Render deploy hook..."; curl -X POST "$${RENDER_DEPLOY_HOOK_URL}"

# --- Quality ---
precommit: ## Install pre-commit hooks
	pre-commit install
	pre-commit run --all-files

all: lint test docker-build docker-up seed ## Full pipeline: lint → test → build → deploy
