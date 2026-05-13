# Ask IRA — CI/CD & Deployment Guide

## Overview

This project uses **GitHub Actions** for CI/CD with four workflows that run automatically on push/PR to `main` and `develop` branches.

| Workflow | File | Trigger | What It Does |
|----------|------|---------|-------------|
| **CI** | `.github/workflows/ci.yml` | Push to `main`/`develop`, PR to `main` | Lint → Audit → Test (3.11 + 3.12) → Docker build → Trivy scan → Smoke test |
| **Deploy** | `.github/workflows/deploy.yml` | Push to `main`, workflow_dispatch | Deploy to Railway, GHCR, Kubernetes, Vercel, Render |
| **Security** | `.github/workflows/security.yml` | Push to `main`/`develop`, weekly Mon 06:00 | CodeQL, Trivy FS scan, pip-audit, Gitleaks secrets detection |
| **PR Checks** | `.github/workflows/pr-checks.yml` | PR open/edit/sync | Size label, conventional commit title check, label validation |

---

## CI Pipeline (`.github/workflows/ci.yml`)

```
Push/PR → Lint (ruff + mypy) → Audit (pip-audit) → Test (pytest 3.11 + 3.12)
  → Docker Build → Trivy Scan → Smoke Test (/health)
```

### Required Secrets for CI

| Secret | Where to Get |
|--------|-------------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

### Steps

1. Push triggers the workflow
2. **Lint**: `ruff check` + `mypy` (optional)
3. **Audit**: `pip-audit` for known CVEs (non-blocking)
4. **Test**: `pytest` with coverage on Python 3.11 + 3.12
5. **Docker build**: multi-stage build from `deployment/Dockerfile`
6. **Trivy scan**: vulnerability scan on built image
7. **Smoke test**: run container, hit `/health` endpoint

---

## Deploy Pipeline (`.github/workflows/deploy.yml`)

### Automatic Deploy Targets (push to `main`)

| Target | Platform | Free Tier | Notes |
|--------|----------|-----------|-------|
| Railway | `railway.app` | $5/mo credit, 512MB RAM | Primary API host |
| GHCR | `ghcr.io` | Unlimited public images | Container registry |
| Kubernetes | Any K8s cluster | K3s/Minikube/Cloud trial | `deployment/kubernetes/*.yaml` |
| Vercel | `vercel.com` | Free tier | Frontend + API proxy |
| Render | `render.com` | 512MB, 750h/mo | Triggered via deploy hook |

### Manual Deploy via `workflow_dispatch`

```bash
# Target specific platform
gh workflow run Deploy --ref main -f environment=railway
# Deploy to all platforms
gh workflow run Deploy --ref main -f environment=all
```

> **Note**: Your GitHub personal access token needs `workflow` scope for `workflow_dispatch`. If it fails with 403, push to `main` instead — the push event triggers automatic deploy.

### Deploy Architecture

```
User Browser
    │
    ├── Vercel (CDN) ── static frontend from src/static/
    │       │
    │       └── Proxy /api/* ──→ Railway (FastAPI backend)
    │
    ├── Railway ── Docker container (uvicorn, 2 workers)
    │       │
    │       ├── PostgreSQL 16 (managed)
    │       └── Redis 7 (managed)
    │
    ├── GHCR ── Container images (amd64 + arm64)
    │
    └── K8s ── Deployment (2 replicas, HPA)
```

---

## Current Deployment Status (May 13, 2026)

Last deploy attempt: commit [`30cb4f3`](https://github.com/npoluri1/ask-ira/actions/runs/25782024163) — `docs: add CI/CD deployment guide`

### Deploy Targets (all failed)

| Target | Status | Root Cause | Fix |
|--------|--------|------------|-----|
| **Railway** | FAILED | Missing `RAILWAY_TOKEN` secret | Generate at Railway dashboard → Tokens → add to GitHub Secrets |
| **Vercel** | FAILED | Missing `VERCEL_TOKEN` secret | Generate at Vercel → Settings → Tokens → add to GitHub Secrets |
| **GHCR** | FAILED | Trivy action `aquasecurity/trivy-action@0.19.0` not found | Pin to `v0.19.0` (add `v` prefix) in deploy.yml |
| **Kubernetes** | FAILED | Missing `KUBECONFIG` secret, no cluster | Disable K8s job or configure cluster |
| **Render** | FAILED | Missing `RENDER_DEPLOY_HOOK_URL` | Generate deploy hook at Render dashboard |

### CI Pipeline (failed — blocked by lint and audit)

| Stage | Status | Root Cause | Fix |
|-------|--------|------------|-----|
| **Lint** | FAILED | ~400+ ruff errors across codebase | Run `ruff check --fix src/ tests/` to auto-fix import sort + unused imports; manually fix E501 (line too long) and E741 (ambiguous `l`) |
| **Audit** | FAILED | `pip-audit --strict` fails on editable local pkg `ask-ira (0.2.0)` | Add `--ignore-pkg ask-ira` flag, OR skip audit for local dev packages |
| **Test** | SKIPPED | Depends on lint passing | Fix lint first |
| **Docker** | SKIPPED | Depends on test passing | Fix test first |

#### Fix lint errors locally

```bash
# Auto-fix import sort + unused imports (most I001, F401 issues)
ruff check --fix src/ tests/

# Count remaining issues
ruff check src/ tests/ --statistics

# Common patterns to fix manually:
# - E501: break long lines (>100 chars) with parentheses or backslash
# - E741: rename variable `l` to something descriptive
# - E402: move module-level imports to top of file
```

#### Fix audit by ignoring local package

Edit `.github/workflows/ci.yml` line 67:

```diff
- pip-audit --strict --progress-spinner=off
+ pip-audit --strict --progress-spinner=off --ignore-pkg ask-ira
```

---

## Required GitHub Secrets — Full Setup

Go to **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Required For | Setup Instructions |
|--------|-------------|-------------------|
| `OPENAI_API_KEY` | CI tests + Runtime LLM calls | OpenAI platform → API keys |
| `RAILWAY_TOKEN` | Railway deploy | Railway dashboard → Tokens → New Token → copy |
| `VERCEL_TOKEN` | Vercel deploy | Vercel dashboard → Settings → Tokens → Create |
| `RENDER_DEPLOY_HOOK_URL` | Render deploy | Render dashboard → Web Services → Deploy Hooks |
| `KUBECONFIG` | K8s deploy | `kubectl config view --raw \| base64` → paste |
| `GITHUB_TOKEN` | GHCR login | Auto-provided by GitHub (no setup needed) |

---

## Fix GHCR Trivy Action Version

Edit `.github/workflows/deploy.yml` — the Trivy action pin is missing the `v` prefix:

```diff
- uses: aquasecurity/trivy-action@0.19.0
+ uses: aquasecurity/trivy-action@v0.19.0
```

This appears in two places in `deploy.yml` (~lines 132 and 140).

---

## Fix Kubernetes Job (optional)

If you don't have a K8s cluster, skip the K8s deploy by removing or commenting out the `deploy-kubernetes` job in `.github/workflows/deploy.yml`. If you do have a cluster:

1. Install `kubectl` locally
2. Copy your kubeconfig contents (base64 encoded)
3. Add as `KUBECONFIG` secret in GitHub

---

## Deploy Checklist

Before deploying, ensure these are configured:

- [ ] `OPENAI_API_KEY` set in GitHub Secrets
- [ ] `RAILWAY_TOKEN` set (sign up at railway.app)
- [ ] `VERCEL_TOKEN` set (sign up at vercel.com)
- [ ] Trivy action pin fixed (`v0.19.0`)
- [ ] K8s job disabled if no cluster
- [ ] `RENDER_DEPLOY_HOOK_URL` set if using Render

---

## Build Steps

### Local Docker Build

```bash
docker build -f deployment/Dockerfile -t ask-ira:latest .
docker run -p 8000:8000 --env-file .env ask-ira:latest
curl http://localhost:8000/health
```

### Docker Compose (full stack)

```bash
docker compose -f deployment/docker-compose.yml up -d
docker compose -f deployment/docker-compose.yml --profile seed run seed
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d
```

### Local Dev (no Docker)

```bash
pip install -e ".[all]"
python -m src.main
```

---

## Security Pipeline (`.github/workflows/security.yml`)

Runs weekly (Mon 06:00 UTC) and on every push:

| Scan | Tool | Scope |
|------|------|-------|
| CodeQL | GitHub CodeQL | Python security + quality queries |
| Filesystem | Trivy | Repo filesystem (HIGH/CRITICAL) |
| Dependencies | pip-audit | Python package CVEs |
| Secrets | Gitleaks | Hardcoded credentials |

---

## PR Checks (`.github/workflows/pr-checks.yml`)

On every PR open/edit:

| Check | Rule |
|-------|------|
| Size label | Auto-labels: XS (≤2), S (≤20), M (≤100), L (≤500), XL (≤1000), XXL (>1000) |
| Title format | Must match `feat\|fix\|docs\|style\|refactor\|perf\|test\|chore\|ci\|build\|revert(scope): description` |
| Labels | Warning if no labels applied |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|------|
| CI fails on lint | ~400+ ruff errors (unused imports, line length, import sort) | Run `ruff check --fix src/ tests/` for auto-fixes; fix E501/E741 manually |
| CI fails on audit | `pip-audit --strict` fails on local editable install | Add `--ignore-pkg ask-ira` to pip-audit in ci.yml |
| CI fails on test | Missing `OPENAI_API_KEY` | Add the secret to GitHub repo |
| Deploy fails on Railway | Missing `RAILWAY_TOKEN` | Generate token at Railway |
| Deploy fails on Vercel | Missing `VERCEL_TOKEN` | Generate token at Vercel |
| Deploy fails on GHCR | Trivy action version typo | Pin to `v0.19.0` with `v` prefix |
| Deploy fails on K8s | No cluster or kubeconfig | Disable K8s job or configure cluster |
| Deploy fails on Render | Missing deploy hook URL | Generate hook at Render dashboard |
| `workflow_dispatch` 403 | PAT lacks `workflow` scope | Push to main instead |
| GHCR login fails | Wrong registry | Ensure `ghcr.io` prefix is correct |

---

## Quick Reference

```bash
git push origin main               # triggers CI + Deploy
git push origin develop             # triggers CI + Security
gh pr create --title "feat: ..."   # triggers CI + PR Checks
git commit -m "docs: [skip ci]"    # skip CI on push
```

---

## Monitoring

- **Health**: `GET /health` (Docker/K8s probes)
- **Metrics**: `GET /metrics` (Prometheus, port 8000)
- **Grafana**: `deployment/docker-compose.monitoring.yml`
- **Logs**: Structured JSON via `src/config/logging.py`
