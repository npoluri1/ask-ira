# MCP Server Standards

Rules for building and maintaining MCP (Model Context Protocol) servers in `src/mcp_servers/`.

## Server Interface

Every MCP server must inherit from `MCPServer` and implement `handle()`:

```python
from src.mcp_servers.base import MCPServer, MCPRequest, MCPResponse

class MyServer(MCPServer):
    async def handle(self, request: MCPRequest) -> MCPResponse:
        return MCPResponse(
            content="result string",
            source="my_server",
            metadata={"key": "value"},
        )
```

## MCPResponse Contract

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | `str` | Yes | Human-readable result text |
| `source` | `str` | Yes | Server name identifier |
| `metadata` | `dict` | No | Structured data for downstream agents |

## Query Routing

Each server must parse the query and route to domain-specific logic:

```python
async def handle(self, request: MCPRequest) -> MCPResponse:
    query = request.query.lower()

    if "keyword_a" in query:
        return await self._handle_a(query)
    elif "keyword_b" in query:
        return await self._handle_b(query)
    else:
        return MCPResponse(
            content="Available queries: keyword_a, keyword_b",
            source="my_server",
        )
```

## Data Loading

1. Use `data/loader.py` for seed data — never hardcode large datasets in server files
2. Load data in `__init__()` for frequently accessed data
3. Use `load_*()` functions, not direct file I/O

```python
class MyServer(MCPServer):
    def __init__(self):
        self.data = load_my_data()  # from data/loader.py
```

## Best Practices

1. **Graceful fallbacks** — If an external API fails, fall back to seed data, don't crash
2. **Tick extraction** — Use `_extract_ticker()` pattern for ticker symbol parsing from free text
3. **Concurrent safety** — Servers must be stateless between `handle()` calls (no per-request state)
4. **Error tolerance** — Each server should return a helpful message even on error
5. **No side effects** — Servers are read-only; never write to databases or filesystems during `handle()`

## Registration

All servers register in `src/mcp_servers/registry.py`:

```python
class MCPRegistry:
    def __init__(self, include_enterprise_db: bool = False):
        self._servers: dict[str, MCPServer] = {
            "my_server": MyServer(),
            ...
        }
```

## Enterprise DB Server Rules

1. Read-only (`SELECT` only) — never allow mutations
2. Mock schema must match live PostgreSQL schema exactly
3. `EnterpriseDBMCPServer` has 8 tables: sectors, companies, analysts, reports, financials, transactions, watchlists, alerts
4. Opt-in via `MCPRegistry(include_enterprise_db=True)`
5. Live mode uses `asyncpg` connection pool when `POSTGRES_DSN` is set
