# Ask IRA — Root Project Rules

This file defines global standards for the Ask IRA codebase. All code must follow these rules unless overridden by a component-specific `.claude/*.md` file.

## Project Overview

Production-grade multi-agent investment research system using LangGraph, MCP, RAG, and FastAPI. 6 agent types, 5 MCP servers, 22 notebooks, 48+ Python source files.

## File Structure Conventions

```
src/
  agents/      # LangGraph nodes (stateful agents)
  api/         # FastAPI routes + models + middleware
  mcp_servers/ # MCP protocol servers
  rag/         # Retrieval-Augmented Generation pipeline
  guardrails/  # Input/output safety filters
  config/      # Settings, prompts, logging, validation
  static/      # Web UI dashboard
  main.py      # FastAPI entry point
  middleware.py # Rate limiting, security headers, request ID
  monitoring.py # Metrics & health tracking
  cache.py     # Response caching layer
  streaming.py # WebSocket streaming manager
```

## Naming Conventions

- **Files**: `snake_case.py` — lowercase with underscores
- **Classes**: `PascalCase` — e.g. `MarketDataMCPServer`, `SupervisorAgent`
- **Functions/Methods**: `snake_case` — e.g. `get_llm()`, `dispatch_all()`
- **Constants**: `UPPER_SNAKE_CASE` — e.g. `BLOCKED_PATTERNS`
- **Private methods**: `_leading_underscore` — e.g. `_parse_plan()`
- **Async functions**: Always `async def` for I/O operations
- **Type hints**: Required on all function signatures and class attributes

## Coding Standards

1. **Type hints** — Every function signature must have typed params and return types
2. **Docstrings** — Only module-level docstrings for complex modules; no inline comments
3. **No comments** — DO NOT add comments to explain obvious code. Write self-documenting code
4. **Imports** — Order: stdlib → third-party → local; one `import` per line; absolute imports preferred
5. **Error handling** — Use specific exceptions, never bare `except:`
6. **Logging** — Use `get_logger(__name__)` from `src.config.logging`, never `print()`
7. **Async** — All I/O-bound code must be async; use `asyncio.gather()` for concurrency
8. **Testing** — Every agent and endpoint must have a corresponding test
9. **Stateless design** — Agents should be stateless where possible; state lives in `AgentState` TypedDict
10. **Configuration** — All config via `Settings` (pydantic-settings), never hardcoded values

## Error Handling

```python
# Good
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

# Bad — bare except, no logging
try: ...
except: ...
```

## Testing Rules

1. Every agent node needs an async test
2. Use `pytest.mark.asyncio` for async tests
3. Mock external APIs (Yahoo Finance, etc.)
4. Test both positive and negative cases (guardrails blocked/pass)
5. `pytest tests/ -v` must pass before merging

## Security Rules

1. Never hardcode secrets — always use `Settings` from `.env`
2. Never log API keys or PII
3. Input guardrails must run before any LLM call
4. Output guardrails must run before any response
5. Rate limiting must apply to all endpoints except `/health`, `/metrics`
6. CORS must be configurable from env, not hardcoded

## Git Rules

1. Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
2. Squash WIP commits before merge
3. Never commit `.env` files, `__pycache__/`, `chroma_db/`

## Architecture Decision Records

- **State machine**: LangGraph `StateGraph` with TypedDict state
- **Agent routing**: Supervisor agent returns JSON `{"next": "agent_name"}` parsed by `_parse_plan()`
- **MCP dispatch**: All servers queried concurrently via `asyncio.gather()`
- **Caching**: `ResponseCache` with `MemoryCache` backend; Redis planned for production
- **RAG**: Hybrid BM25 + dense → RRF fusion → cross-encoder reranking
- **Deployment**: Multi-target (Docker, K8s, Railway) with GitHub Actions CI/CD
