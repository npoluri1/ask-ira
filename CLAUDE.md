# Ask IRA — Complete Project Reference

## Project Overview

Production-grade multi-agent investment research + fintech super-app. LangGraph agent orchestration, 13 LLM providers, MCP data servers, RAG pipeline, enterprise cybersecurity, and a full financial services platform (banking, payments, crypto, insurance, compliance, wallets, portfolio management).

- **Version**: 0.5.0
- **Python**: >=3.11
- **Entry**: `src/main.py` (FastAPI)
- **Frontend**: SPA at `/ui/` (Vercel), API on Railway

## Architecture

```
User (Browser/API)
  │
  ├── Vercel (CDN) ── static frontend (index.html → app.js → fetch)
  │
  └── Railway (FastAPI)
        ├── Core Routes: /api/v1/query, /api/v1/config/*, /api/v1/auth/*
        ├── Market Routes: /api/v1/market/*
        ├── Fintech Routes: /api/v1/{banking,payments,crypto,compliance,wallets,portfolio,security,insurance}/*
        ├── System: /health, /metrics, /api/v1/system/capabilities
        │
        ├── Agent Graph (LangGraph)
        │   └── supervisor → researcher → analyst → critic (loop) → portfolio_manager → risk_assessor → writer → critic → compliance → output
        │
        ├── MCP Servers (data sources)
        │   ├── market_data (yfinance)
        │   ├── macro (FRED + yfinance)
        │   ├── sentiment (yfinance news)
        │   ├── internal_kb (local JSON)
        │   └── enterprise_db (mock PostgreSQL)
        │
        ├── RAG Pipeline
        │   └── query_expansion → hybrid_retrieval(BM25+vector) → RRF_fusion → cross_encoder_rerank
        │
        ├── Guardrails
        │   ├── input: insider trading, PII, market manipulation, length checks
        │   └── output: hallucination markers, confidential content
        │
        └── Security Layer
            └── WAF + IDS + SIEM + DDoS + Threat Intel + RBAC + MFA + Rate Limiting
```

## MCP Tools for Dynamic Data Fetching

When working on this project, use these MCP tool patterns to get real-time data from the internet for any feature/menu:

### Market Data (any ticker/symbol)
```
GET /api/v1/market/indices       → Global indices (S&P 500, Nifty, Nikkei, etc.)
GET /api/v1/market/stocks        → Top stocks by volume
GET /api/v1/market/stocks/{ticker} → Single stock detail
GET /api/v1/market/forex         → Major forex pairs
GET /api/v1/market/crypto        → Top cryptocurrencies
GET /api/v1/market/commodities   → Commodities (gold, oil, etc.)
GET /api/v1/market/bonds         → Bond yields
GET /api/v1/market/movers        → Top gainers/losers
GET /api/v1/market/news          → Financial news
SSE /api/v1/market/live          → Real-time streaming
```

### AI Research (multi-agent query)
```
POST /api/v1/query  { query, session_id, risk_profile }
  → returns: report, analysis, confidence, mcp_results, portfolio_allocation, risk_assessment
```

### Fintech Services (all require underlying domain modules)
```
Banking:   GET /api/v1/banking/{accounts,transfers,loans,deposits,cards,bills}
Payments:  GET /api/v1/payments/  + /swift/banks, /sepa/mandates, /ach/routes, /faster/limits
Wallets:   GET /api/v1/wallets/{banking,crypto,insurance}
Insurance: GET /api/v1/insurance/{policies,claims,premiums}
Compliance: GET /api/v1/compliance/{countries,score}
Security:  GET /api/v1/security/{waf,ids,siem,ddos}/stats
```

### System
```
GET /api/v1/config/data-source         → Current mode (realtime/seed)
POST /api/v1/config/data-source/toggle → Toggle AI vs Live data
GET /api/v1/insights/{section}         → AI-generated insights per page
```

## Complete Menu Structure (24 Navigation Items)

### Markets Group
| Menu | Page ID | Backend Endpoint | Data Source |
|------|---------|-----------------|-------------|
| Dashboard | `dashboard` | `GET /market/indices + /market/movers + /market/news + SSE` | yfinance + FRED |
| AI Research | `research` | `POST /query` | LangGraph agents + MCP |
| Stocks | `stocks` | `GET /market/stocks + POST /query` | yfinance |
| Indices | `indices` | `GET /market/indices` | yfinance |
| Forex | `forex` | `GET /market/forex` | yfinance |
| Crypto | `crypto` | `GET /market/crypto` | yfinance |
| Commodities | `commodities` | `GET /market/commodities` | yfinance |

### Investments Group
| Menu | Page ID | Backend Endpoint | Data Source |
|------|---------|-----------------|-------------|
| Funds & ETFs | `funds` | `POST /query` | LangGraph agents |
| Bonds | `bonds` | `GET /market/bonds` | yfinance |
| Options & Futures | `options` | `POST /query` | LangGraph agents |
| IPOs | `ipos` | Static (hardcoded) | — |

### Portfolio Group
| Menu | Page ID | Backend Endpoint | Data Source |
|------|---------|-----------------|-------------|
| My Portfolio | `portfolio` | localStorage | Client-side only |
| Watchlist | `watchlist` | localStorage | Client-side only |
| Compare | `compare` | `POST /query` | LangGraph agents |
| Risk Analysis | `risk` | `POST /query` | LangGraph agents |
| Market Screener | `screener` | `POST /query` | LangGraph agents |

### Account Group
| Menu | Page ID | Backend Endpoint | Data Source |
|------|---------|-----------------|-------------|
| Alerts | `alerts` | localStorage | Client-side only |
| Settings | `settings` | `GET/POST /config/data-source` | Config API |

### Financial Services Group
| Menu | Page ID | Backend Endpoint | Data Source |
|------|---------|-----------------|-------------|
| Banking | `banking` | `GET /banking/*` (7 endpoints) | Domain module needed |
| Payments | `payments` | `GET /payments/*` (6 endpoints) | Domain module needed |
| Wallets | `wallets` | `GET /wallets/*` (3 endpoints) | Domain module needed |
| Insurance | `insurance` | `GET /insurance/*` (3 endpoints) | Domain module needed |
| Compliance | `compliance` | `GET /compliance/*` (2 endpoints) | Domain module needed |
| Security | `security` | `GET /security/*` (4 endpoints) | Cybersecurity engine |

## Project Structure

```
src/
├── main.py                  # FastAPI app, lifespan, middleware, route mounting
├── auth.py                  # JWT tokens, password hashing, USER_DB
├── security.py              # RBAC (7 roles), sessions, MFA, API keys, audit
├── cybersecurity.py         # WAF (10 categories), IDS (8 rules), SIEM, DDoS, Scanner
├── middleware.py            # RateLimit, RequestID, SecurityHeaders middleware
├── monitoring.py            # Prometheus metrics, health check
├── cache.py                 # MemoryCache + ResponseCache
├── streaming.py             # WebSocket ConnectionManager + stream_research()
├── agent_platform.py        # Generic agent registry (20 types), mesh, ledger, governor
├── compliance_router.py     # 18-country compliance rules engine
├── portfolio.py             # Portfolio calculation, rebalancing, diversification
├── trade_execution.py       # Trade execution, position sizing, approvals
│
├── api/                     # FastAPI route definitions (12 route files)
│   ├── routes.py            # Core: /api/v1/query, /api/v1/config/*
│   ├── market_routes.py     # /api/v1/market/* (10 endpoints + SSE)
│   ├── auth_routes.py       # /api/v1/auth/* (6 endpoints)
│   ├── banking_routes.py    # /api/v1/banking/* (30+ endpoints)
│   ├── payments_routes.py   # /api/v1/payments/* (15+ endpoints)
│   ├── crypto_routes.py     # /api/v1/crypto/* (20+ endpoints)
│   ├── compliance_routes.py # /api/v1/compliance/* (15+ endpoints)
│   ├── wallets_routes.py    # /api/v1/wallets/* (15+ endpoints)
│   ├── portfolio_routes.py  # /api/v1/portfolio/* (15+ endpoints)
│   ├── security_routes.py   # /api/v1/security/* (15+ endpoints)
│   ├── insurance_routes.py  # /api/v1/insurance/* (8 endpoints)
│   ├── models.py            # QueryRequest, QueryResponse
│   ├── middleware.py         # RequestLoggingMiddleware
│   └── fallback_query.py    # AI-generated fallback data (75 stocks, indices, etc.)
│
├── agents/                  # LangGraph agents (9 node types)
│   ├── state.py             # AgentState TypedDict (18 fields)
│   ├── graph.py             # StateGraph (11 nodes, conditional edges)
│   ├── supervisor.py        # Routes queries to MCP servers
│   ├── researcher.py        # Gathers data via MCP + RAG
│   ├── analyst.py           # Investment analysis with confidence scoring
│   ├── writer.py            # Markdown report generation
│   ├── critic.py            # Quality review (analysis + report)
│   ├── portfolio_manager.py # Asset allocation (3 risk profiles)
│   ├── risk_assessor.py     # VaR, drawdown, risk scoring
│   └── compliance.py        # Regulatory keyword + disclaimer checks
│
├── mcp_servers/             # MCP protocol data servers
│   ├── base.py              # Abstract MCPServer, MCPRequest, MCPResponse
│   ├── registry.py          # MCPRegistry (concurrent dispatch)
│   ├── market_data.py       # yfinance: prices, financials, SEC filings
│   ├── macro.py             # FRED: GDP, CPI, rates, employment
│   ├── sentiment.py         # yfinance news + lexicon sentiment
│   ├── internal_kb.py       # Local knowledge base keyword matching
│   └── enterprise_db.py     # Mock 8-table PostgreSQL schema
│
├── rag/                     # Retrieval-Augmented Generation
│   ├── pipeline.py          # RAGPipeline orchestration
│   ├── retrieval.py         # HybridRetriever (BM25 0.3 + vector 0.7), RRF fusion
│   ├── vector_store.py      # ChromaDB wrapper
│   ├── embeddings.py        # HuggingFace / OpenAI / dummy fallback
│   └── reranking.py         # CrossEncoderReranker (ms-marco-MiniLM)
│
├── guardrails/              # Input/output safety filters
│   ├── input.py             # Blocks: insider trading, PII, manipulation, length
│   └── output.py            # Blocks: hallucination markers, confidential content
│
├── config/                  # Configuration
│   ├── settings.py          # pydantic-settings (50+ fields)
│   ├── logging.py           # Structured JSON logging
│   ├── prompts.py           # 4 prompt templates (research, analysis, writing, review)
│   ├── validation.py        # Provider API key checks
│   └── data_source.py       # Data source toggle (realtime vs seed)
│
├── utils/
│   ├── llm.py               # LLM factory — 13 providers
│   └── callbacks.py         # LangSmith tracing
│
├── banking/                 # Domain: accounts, transfers, loans, deposits, cards, bills
├── payments/                # Domain: engine, swift, sepa, ach, faster_payments, rails
├── crypto/                  # Domain: wallets, transactions, staking, defi, compliance
├── compliance/              # Domain: aml, kyc, sanctions, reporting
├── insurance/               # Domain: policies, claims, premiums
├── wallets/                 # Domain: banking_wallet, crypto_wallet, insurance_wallet
├── products/                # Domain: mutual_funds, fixed_deposits, annuities, sip
│
└── static/                  # Frontend SPA (served at /ui/)
    ├── index.html           # 553 lines — single-page app shell
    ├── css/style.css        # 374 lines — dark theme
    ├── js/api.js            # 202 lines — REST client w/ JWT + auto-refresh
    ├── js/app.js            # 891 lines — UI logic, Chart.js, SSE consumer
    ├── manifest.json        # PWA manifest
    └── sw.js                # Service worker (offline cache)

data/                         # Seed data + infrastructure
├── *.json                   # 10+ JSON seed files (companies, metrics, news, etc.)
├── chroma/                  # ChromaDB vector store
├── sample_reports/          # 5 sample markdown reports
├── postgres/init/           # 01_schema.sql (8 tables)
├── grafana/                 # Grafana dashboard config
└── prometheus/              # prometheus.yml

tests/                        # 13 test files
├── test_api.py              # Root, health, metrics, query endpoints
├── test_agents.py           # MCP registry + server dispatch
├── test_agents_unit.py      # All agent types (unit tests)
├── test_graph.py            # StateGraph creation + AgentState
├── test_rag.py              # RRF fusion, vector store
├── test_mcp_servers.py      # Registry, enterprise DB
├── test_config.py           # Settings, prompts, validation
├── test_middleware.py       # Security headers, CORS, request ID
├── test_models.py           # Pydantic models
├── test_monitoring.py       # Health + metrics
├── test_cache.py            # MemoryCache + ResponseCache
└── test_streaming.py        # ConnectionManager

deployment/                   # Infrastructure as code
├── Dockerfile / Dockerfile.dev
├── docker-compose.yml / .override.yml / .monitoring.yml
├── kubernetes/              # deployment, configmap, secrets, ingress, hpa
└── ...

.github/workflows/           # CI/CD
├── ci.yml                   # Lint → audit → test (3.11/3.12) → Docker build
├── deploy.yml               # Multi-target: Railway, GHCR, K8s, Vercel, Render
├── security.yml             # Security scanning
└── pr-checks.yml            # PR validation

notebooks/                    # 21 Jupyter notebooks (fundamentals → ML → capstone)
```

## Naming Conventions

| Category | Style | Example |
|----------|-------|---------|
| Files | `snake_case.py` | `market_routes.py` |
| Classes | `PascalCase` | `MarketDataMCPServer` |
| Functions/Methods | `snake_case` | `get_llm()` |
| Constants | `UPPER_SNAKE_CASE` | `BLOCKED_PATTERNS` |
| Private methods | `_leading_underscore` | `_parse_plan()` |
| Async I/O | `async def` | `async def fetch_price()` |
| Type hints | Required everywhere | `def get(x: str) -> float:` |

## Coding Standards

1. **Type hints** — every function signature: typed params + return type
2. **Docstrings** — module-level only for complex modules; no inline comments
3. **No comments** — write self-documenting code
4. **Imports** — stdlib → third-party → local; one per line; absolute preferred
5. **Error handling** — specific exceptions, never bare `except:`
6. **Logging** — `get_logger(__name__)` from `src.config.logging`, never `print()`
7. **Async** — all I/O via `async def` + `asyncio.gather()`; never blocking calls
8. **Testing** — every agent + endpoint must have a test
9. **Stateless agents** — state lives in `AgentState` TypedDict
10. **Configuration** — via `Settings` (pydantic-settings), never hardcoded

## Error Handling Pattern
```python
async def fetch_stock_price(ticker: str) -> float:
    try:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()["price"]
    except httpx.TimeoutException:
        logger.warning("Timeout fetching %s, using fallback", ticker)
        return FALLBACK_PRICE
    except (KeyError, httpx.HTTPError) as e:
        logger.error("Failed to fetch %s: %s", ticker, e)
        raise
```

## Testing Rules
1. Every agent node needs an async test
2. Use `pytest.mark.asyncio` for async tests
3. Mock external APIs (yfinance, FRED)
4. Test both positive + negative guardrail cases
5. `pytest tests/ -v` must pass before merging
6. Run: `pytest tests/ -v --cov=src --cov-report=term-missing`

## Security Rules
1. Never hardcode secrets — always use `Settings` from `.env`
2. Never log API keys or PII
3. Input guardrails before every LLM call
4. Output guardrails before every response
5. Rate limiting on all endpoints except `/health`, `/metrics`
6. CORS configurable from env

## Git Rules
1. Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
2. Squash WIP commits before merge
3. Never commit `.env`, `__pycache__/`, `chroma_db/`

## LLM Provider Ecosystem (13 supported)

| Tier | Providers |
|------|-----------|
| **Free** (no CC) | Groq (Llama 3, 30/min), Gemini 1.5 Flash (60/min), Ollama (local), HuggingFace (Zephyr), OpenRouter (200+ models), DeepSeek ($0.14/M), Mistral (Small/Medium), Together AI ($25 credits), Fireworks AI |
| **Paid** | OpenAI GPT-4o (default), Anthropic Claude, Replicate |
| **Factory** | `src/utils/llm.py` → `get_llm(provider, model, temperature, streaming)` → `BaseChatModule` |

## MCP Server Data Sources

| Server | Live API | Seed Fallback | Rate |
|--------|----------|---------------|------|
| `market_data` | yfinance | `financial_metrics.json` | ~1s/ticker |
| `macro` | FRED + yfinance | `macro_indicators.json` | 15s timeout |
| `sentiment` | yfinance news | `news_articles.json` | ~1s |
| `internal_kb` | Local JSON | `knowledge_base.json` | instant |
| `enterprise_db` | Mock/asyncpg | 8-table mock schema | instant |

## Agent Graph Flow

```
START → guard_input (blocked? → END)
  → supervisor (routing plan)
  → researcher (MCP dispatch + RAG)
  → analyst (analysis + confidence)
  → critic_analysis (quality check, loop up to 2x)
  → portfolio_manager (asset allocation, 3 risk profiles)
  → risk_assessor (VaR, drawdown, risk score)
  → writer (markdown report)
  → critic_report (quality check)
  → compliance (regulatory + disclaimer)
  → human_review (optional, auto-checks)
  → guard_output → END
```

**AgentState** (18 fields): query, messages, plan, dimensions, servers, use_rag, mcp_results, rag_context, analysis, synthesis, report, confidence, next, iteration, risk_profile, portfolio_allocation, risk_assessment, critique, compliance_result, human_approved

## Compliance Router — 18 Supported Countries

US, UK, EU, UAE, SG, HK, IN, JP, AU, SA, CH, BR, CN, ZA, MX, CA

Each with: regulators, KYC level, AML checks, SAR threshold, data retention, privacy law, reporting obligations, crypto rules, insurance rules, restrictions.

## Frontend API Client Patterns (`src/static/js/api.js`)

All API calls go through the `API` object:
- JWT token stored in localStorage (`ira_access_token`)
- Auto-refresh via `ira_refresh_token`
- All GET requests have TTL-based caching (30s-120s)
- SSE stream at `GET /api/v1/market/live` for real-time updates (indices, stocks, forex, crypto, news, insights)
- localStorage-only features (no API): Portfolio, Watchlist, Alerts, Settings

Key API methods:
```javascript
API.query(payload)       // POST /api/v1/query — main AI research
API.getIndices()         // GET /api/v1/market/indices — 60s TTL
API.getMovers()          // GET /api/v1/market/movers — 60s TTL
API.getNews()            // GET /api/v1/market/news — 120s TTL
API.getDataSource()      // GET /api/v1/config/data-source
API.toggleDataSource()   // POST /api/v1/config/data-source/toggle
API.getInsights(section) // GET /api/v1/insights/{section}
API.getAccounts()        // GET /api/v1/banking/accounts
API.getPayments()        // GET /api/v1/payments/
API.getWafStats()        // GET /api/v1/security/waf/stats
```

## Deployment Architecture

| Component | Platform | Config |
|-----------|----------|--------|
| Frontend (static) | Vercel | `vercel.json` (rewrite rules) |
| Backend (API) | Railway | `railway.json` (Docker) |
| Container | Docker | `deployment/Dockerfile` (multi-stage) |
| Orchestration | K8s | `deployment/kubernetes/*.yaml` (2 replicas + HPA) |
| CI/CD | GitHub Actions | `.github/workflows/{ci,deploy,security,pr-checks}.yml` |

## Key Config Settings (`src/config/settings.py`)

- `llm_provider`: default `"openai"`, 12+ API key fields
- `data_source`: `"realtime"` or `"seed"`
- `environment`: `"development"` (default) or `"production"`
- `chroma_persist_dir`: `"./data/chroma"`
- `embedding_model`: `"sentence-transformers/all-MiniLM-L6-v2"`
- `cache_enabled`: `True`, `cache_ttl_mcp`: 300, `cache_ttl_rag`: 600
- `rate_limit_max`: 100, `rate_limit_window`: 60
- `jwt_secret`: (required), `jwt_expire_minutes`: 60
- `mfa_enabled`: `True`, `session_timeout_minutes`: 60
- `default_compliance_country`: `"US"`
- `multi_tenant_enabled`: `False`

## Quickstart Commands

```bash
# Install
pip install -e ".[all]"

# Run development
python -m src.main

# Tests
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term-missing

# Docker
docker compose up --build

# Lint
ruff check src/ tests/
ruff format --check src/ tests/
```

## Architecture Decision Records

- **State machine**: LangGraph `StateGraph` with TypedDict state
- **Agent routing**: Supervisor returns JSON `{"next": "agent_name"}` parsed by `_parse_plan()`
- **MCP dispatch**: All 5 servers queried concurrently via `asyncio.gather()`
- **Caching**: `ResponseCache` with `MemoryCache` backend; Redis planned
- **RAG**: Hybrid BM25 (0.3) + dense (0.7) → RRF fusion → cross-encoder reranking
- **Data source toggle**: Realtime (live APIs) vs Seed (local JSON) — toggleable at runtime
- **Security**: Layered defense — WAF + IDS + SIEM + DDoS + InputSanitizer + VulnerabilityScanner
- **Auth**: JWT access/refresh tokens + session management + MFA + RBAC (7 roles)
- **Frontend**: SPA with localStorage state, SSE for live data, Chart.js for visualization
