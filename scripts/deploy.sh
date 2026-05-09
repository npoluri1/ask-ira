#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Ask IRA — One-Click Deploy Script
# =============================================================================
# Usage:
#   ./scripts/deploy.sh                    # Docker Compose (local)
#   ./scripts/deploy.sh compose            # Docker Compose (local)
#   ./scripts/deploy.sh compose-dev        # Docker Compose with hot-reload
#   ./scripts/deploy.sh compose-monitoring # Docker Compose + Prometheus + Grafana
#   ./scripts/deploy.sh seed               # Seed vector store data
#   ./scripts/deploy.sh k8s                # Kubernetes
#   ./scripts/deploy.sh railway            # Railway (free tier)
#   ./scripts/deploy.sh vercel             # Vercel (free tier, REST only)
#   ./scripts/deploy.sh render             # Render (free tier)
#   ./scripts/deploy.sh build              # Build Docker image only
#   ./scripts/deploy.sh all                # Build + Docker Compose + seed
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

TARGET="${1:-compose}"

case "$TARGET" in
  compose)
    info "Deploying with Docker Compose..."
    docker compose -f deployment/docker-compose.yml up --build -d
    info "API: http://localhost:8000"
    info "Docs: http://localhost:8000/docs"
    info "Dashboard: http://localhost:8000/ui"
    ;;

  compose-monitoring)
    info "Deploying full stack with monitoring..."
    docker compose -f deployment/docker-compose.yml \
      -f deployment/docker-compose.monitoring.yml \
      --profile monitoring up --build -d
    info "API:     http://localhost:8000"
    info "Grafana: http://localhost:3000 (admin/admin)"
    info "Prom:    http://localhost:9090"
    ;;

  compose-dev)
    info "Deploying with dev overrides (hot-reload)..."
    docker compose -f deployment/docker-compose.yml \
      -f deployment/docker-compose.override.yml up --build -d
    info "API (live-reload): http://localhost:8000"
    info "Adminer (DB UI):   http://localhost:8080"
    ;;

  seed)
    info "Running seed data into vector store..."
    docker compose -f deployment/docker-compose.yml \
      --profile seed run --rm seed
    ;;

  build)
    info "Building production Docker image..."
    docker build -f deployment/Dockerfile -t ask-ira:latest .
    info "Build complete: ask-ira:latest"
    ;;

  k8s|kubernetes)
    info "Deploying to Kubernetes..."
    command -v kubectl &>/dev/null || { error "kubectl not found"; exit 1; }
    kubectl apply -f deployment/kubernetes/configmap.yaml
    kubectl apply -f deployment/kubernetes/secrets.yaml
    kubectl apply -f deployment/kubernetes/deployment.yaml
    kubectl apply -f deployment/kubernetes/hpa.yaml
    kubectl apply -f deployment/kubernetes/ingress.yaml
    kubectl rollout status deployment/ask-ira --timeout=120s
    info "K8s deploy complete!"
    ;;

  railway)
    info "Deploying to Railway (free tier)..."
    command -v railway &>/dev/null || { npm install -g @railway/cli; }
    [ -n "${RAILWAY_TOKEN:-}" ] || { error "RAILWAY_TOKEN not set"; exit 1; }
    railway up --service ask-ira --detach
    info "Railway deploy initiated!"
    ;;

  vercel)
    info "Deploying to Vercel (free tier, REST only)..."
    command -v vercel &>/dev/null || { npm install -g vercel; }
    vercel deploy --prod --yes
    info "Vercel deploy initiated!"
    ;;

  render)
    info "Deploying to Render (free tier)..."
    [ -n "${RENDER_DEPLOY_HOOK_URL:-}" ] || { error "RENDER_DEPLOY_HOOK_URL not set"; exit 1; }
    curl -X POST "$RENDER_DEPLOY_HOOK_URL"
    info "Render deploy triggered!"
    ;;

  all)
    info "=== Full Local Deploy ==="
    docker build -f deployment/Dockerfile -t ask-ira:latest .
    docker compose -f deployment/docker-compose.yml up --build -d
    info "=== Local Deploy Complete ==="
    echo "  API:        http://localhost:8000"
    echo "  Docs:       http://localhost:8000/docs"
    echo "  Health:     http://localhost:8000/health"
    echo "  Dashboard:  http://localhost:8000/ui"
    ;;

  *)
    echo "Usage: $0 [compose|compose-dev|compose-monitoring|seed|build|k8s|railway|vercel|render|all]"
    exit 1
    ;;
esac
