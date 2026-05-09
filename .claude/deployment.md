# Deployment Standards

Rules for Docker, Kubernetes, Railway, and CI/CD configuration in `deployment/` and `.github/workflows/`.

## Docker Build Standards

### Multi-stage Build (`deployment/Dockerfile`)

```
Stage 1: builder (python:3.11-slim)
  → Install build-essential + compilers
  → pip install --prefix=/install -e ".[mcp,eval]"

Stage 2: runtime (python:3.11-slim)
  → Copy /install from builder
  → Create non-root 'askira' user
  → Set HEALTHCHECK (curl /health, 30s interval)
  → EXPOSE 8000
  → CMD: uvicorn src.main:app --workers 2
```

### Dockerfile Rules

1. Always use multi-stage builds to minimize image size
2. Run as non-root user — never as root
3. Include `HEALTHCHECK` pointing to `/health`
4. Pin base image versions (e.g., `python:3.11-slim`, not `python:latest`)
5. Use `.dockerignore` to exclude `__pycache__/`, `.env`, `chroma_db/`, `.git/`
6. Development image (`Dockerfile.dev`) uses hot-reload with volume mounts

## Docker Compose Standards

### Services

| Service | Image | Purpose | Depends On |
|---------|-------|---------|------------|
| `api` | `ask-ira:latest` | FastAPI application | postgres, redis |
| `postgres` | `postgres:16-alpine` | Enterprise database | — |
| `redis` | `redis:7-alpine` | Response caching | — |
| `seed` | `ask-ira:latest` (profile) | ChromaDB seeding | postgres |

### Compose Rules

1. Use healthchecks on all services
2. Pin image versions (never `:latest` for external images)
3. Resource limits (memory) for all services
4. Named volumes for persistent data (pgdata, chromadb_data, redis_data)
5. Seed service uses `profiles: [seed]` — only runs on explicit `--profile seed`
6. Environment variables from `.env` file + overrides in compose

## Kubernetes Standards

### Required Manifests

| Manifest | Purpose |
|----------|---------|
| `deployment.yaml` | 3 replicas, rolling update, resource limits |
| `hpa.yaml` | CPU >70% or memory >80% → scale 2-10 pods |
| `ingress.yaml` | nginx ingress with TLS termination |
| `configmap.yaml` | Non-sensitive env vars |
| `secrets.yaml` | API keys (Base64 encoded) |

### K8s Rules

1. Never store secrets in ConfigMap — use Secrets
2. Requests < Limits for all containers
3. Rolling update strategy (maxSurge=1, maxUnavailable=0)
4. Readiness + liveness probes on the API container
5. Pod anti-affinity for high availability

## Railway Standards

### Configuration (`railway.json`)

```json
{
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "deployment/Dockerfile" },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "sleepApplication": false
  }
}
```

## CI/CD Standards

### CI Workflow (`.github/workflows/ci.yml`)

```
Jobs:
  1. lint: ruff check src/ tests/ scripts/  (py311)
  2. test (matrix: py311, py312): pytest --cov=src
  3. docker-build (if main): Docker Buildx → smoke test (curl /health)
```

### CD Workflow (`.github/workflows/deploy.yml`)

```
Jobs:
  1. deploy-railway: railway up --service ask-ira --detach
  2. deploy-docker: buildx multi-arch → push to Docker Hub
```

### Secrets Required

| Secret | Used By |
|--------|---------|
| `RAILWAY_TOKEN` | Railway deploy |
| `DOCKER_USERNAME` | Docker Hub push |
| `DOCKER_PASSWORD` | Docker Hub push |
| `ANTHROPIC_API_KEY` | Runtime |
| `OPENAI_API_KEY` | Runtime |

### CI/CD Rules

1. Lint before test, test before build
2. Matrix test across Python 3.11 and 3.12
3. Docker smoke test must pass before deploy
4. CD runs only on push to `main`
5. Manual dispatch available for Railway vs Docker selection

## Environment Configuration

### Required Files

- `.env.example` — template with all variables documented
- `.env` — actual values (gitignored)
- `deployment/kubernetes/configmap.yaml` — non-sensitive
- `deployment/kubernetes/secrets.yaml` — sensitive (gitignored in real deployments)

### Environment Variables

All config via `src/config/settings.py` (pydantic-settings). Must have sensible defaults for development but fail fast in production.

```python
class Settings(BaseSettings):
    anthropic_api_key: str = ""  # Must be set in production
    environment: str = "development"  # Changes behavior: mock vs live
    model_config = {"env_file": ".env"}
```

## Monitoring Stack

### Prometheus + Grafana (`deployment/docker-compose.monitoring.yml`)

- Prometheus scrapes the API `/metrics` endpoint
- Grafana dashboards for request rate, latency, error rate
- Default credentials: admin/admin
- Not included in default `docker compose up` — opt-in with `-f monitoring.yml`
