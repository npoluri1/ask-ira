# MCP Enterprise Database: Demo & Integration Guide

The Enterprise DB MCP Server provides read-only database access to an 8-table enterprise schema through the Model Context Protocol. It works in two modes:

1. **Mock mode** (default) — 50+ pre-seeded rows, no database required
2. **Live mode** — asyncpg connection to PostgreSQL when `POSTGRES_DSN` is set

## Schema Overview

```
sectors (5) ──→ companies (10) ──→ financials (6)
                    │                   
                    ├──→ reports (4) ──→ analysts (4)
                    ├──→ transactions (4)
                    ├──→ alerts (3)
watchlists (3)
```

| Table | Rows | Description |
|-------|------|-------------|
| `sectors` | 5 | Technology, Financials, Healthcare, Consumer, Energy |
| `companies` | 10 | AAPL, MSFT, GOOGL, AMZN, JPM, GS, JNJ, PFE, TSLA, XOM |
| `analysts` | 4 | Hanu Madala, Shankar Cherukuri, Priya Sharma, Michael Chen |
| `reports` | 4 | Research reports with ratings and target prices |
| `financials` | 6 | Quarterly revenue, net income, EPS, FCF |
| `transactions` | 4 | Insider buy/sell transactions |
| `watchlists` | 3 | Themed watchlists by analyst |
| `alerts` | 3 | Price target, earnings, news alerts |

## Querying via MCP

### Available Tools

| Query Pattern | Description |
|---------------|-------------|
| `list tables` or `schema` | List all available tables |
| `describe <table>` | Show columns and row count |
| `query <table>` or `select <table>` | Show data sample (5 rows) |
| `sample <table>` or `preview <table>` | Show first 3 rows |

### Examples

```
User: list tables
Agent: Available tables (8): sectors, companies, analysts, reports, financials, transactions, watchlists, alerts

User: describe companies
Agent: Table 'companies': columns=['id', 'ticker', 'name', 'sector_id', 'market_cap', 'employees'], rows=10

User: query financials
Agent: Table 'financials' (6 rows, showing 5):
  id | company_id | fiscal_quarter | fiscal_year | revenue | net_income | eps | fcf
  ---|------------|---------------|-------------|---------|------------|-----|-----
  1  | 1          | Q1            | 2025        | 124300000000 | 34500000000 | 2.40 | 28500000000
  ...

User: sample transactions
Agent: [{'id': 1, 'company_id': 1, 'transaction_type': 'BUY', 'shares': 5000, ...}]
```

## Using in the Agent Graph

The Enterprise DB server is **opt-in** — not loaded by default to keep startup fast:

```python
from src.mcp_servers.registry import MCPRegistry

# Without enterprise DB (default — 4 servers)
registry = MCPRegistry()

# With enterprise DB (5 servers)
registry = MCPRegistry(include_enterprise_db=True)
```

The supervisor agent will route queries containing table-related keywords (e.g., "show me analysts", "list companies") to the enterprise DB server.

## Connecting to Live PostgreSQL

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Set the DSN

```bash
export POSTGRES_DSN=postgresql://askira:password@localhost:5432/askira
```

### 3. Run with Live DB

When `POSTGRES_DSN` is set and non-empty, `EnterpriseDBMCPServer` automatically attempts an `asyncpg` connection pool. Falls back to mock data if connection fails.

The init SQL is at `data/postgres/init/01_schema.sql` and auto-runs on first container start (Docker).

## Schema SQL

```sql
-- 8 tables with foreign keys, indexes, and constraints
-- Full schema at: data/postgres/init/01_schema.sql

CREATE TABLE sectors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(5) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    sector_id INTEGER REFERENCES sectors(id),
    market_cap BIGINT,
    employees INTEGER
);

-- ... (6 more tables: analysts, reports, financials, transactions, watchlists, alerts)
```

## Testing

```python
from src.mcp_servers.registry import MCPRegistry

registry = MCPRegistry(include_enterprise_db=True)
server = registry.get_server("enterprise_db")

# List tables
result = await server.handle(MCPRequest(query="list tables"))
print(result.content)
# → "Available tables (8): sectors, companies, analysts, reports, financials, transactions, watchlists, alerts"

# Describe a table
result = await server.handle(MCPRequest(query="describe analysts"))
print(result.content)
# → "Table 'analysts': columns=['id', 'first_name', 'last_name', 'firm', 'sector_focus', 'years_exp'], rows=4"

# Query data
result = await server.handle(MCPRequest(query="query companies"))
print(result.content)
# → "Table 'companies' (10 rows, showing 5):..."
```

## MCP Client Configuration

The enterprise DB server is included in all 3 MCP client config formats:

- `.mcp.json` (Claude Code CLI) — uncomment the `enterprise_db` entry
- `cline-mcp-config.json` (Cline) — uncomment the `enterprise_db` entry  
- `.vscode/mcp.json` (VS Code Copilot) — uncomment the `enterprise_db` entry

Each config file has the enterprise DB server commented out by default. Uncomment to enable.
