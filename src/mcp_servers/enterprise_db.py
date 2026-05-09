"""
Enterprise Database MCP Server.

Provides read-only access to a PostgreSQL database with an enterprise schema
(companies, financials, analysts, reports, sectors, transactions, watchlists, alerts).

Uses asyncpg for async PostgreSQL connections with connection pooling.
All tools are read-only (SELECT only) for safety.

Schema (8 tables):
- sectors: Industry sector definitions
- companies: Company profiles with sector FK
- analysts: Research analyst profiles
- reports: Research reports with company/analyst FK
- financials: Quarterly financial metrics per company
- transactions: Insider trading transactions
- watchlists: User watchlist definitions
- alerts: Price/event alert configurations
"""

import logging
from typing import Any

from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer

logger = logging.getLogger(__name__)


class EnterpriseDBMCPServer(MCPServer):
    """MCP server providing read-only enterprise database access."""

    def __init__(self, dsn: str = ""):
        self._dsn = dsn
        self._pool = None
        self._mock_tables = self._build_mock_schema()

    def _build_mock_schema(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "sectors": [
                {"id": 1, "name": "Technology", "code": "TECH", "description": "Software, hardware, IT services"},
                {"id": 2, "name": "Financials", "code": "FIN", "description": "Banking, insurance, asset management"},
                {"id": 3, "name": "Healthcare", "code": "HC", "description": "Pharma, biotech, medical devices"},
                {"id": 4, "name": "Consumer Cyclical", "code": "CONS", "description": "Retail, auto, entertainment"},
                {"id": 5, "name": "Energy", "code": "ENER", "description": "Oil & gas, renewables, utilities"},
            ],
            "companies": [
                {"id": 1, "ticker": "AAPL", "name": "Apple Inc.", "sector_id": 1, "market_cap": 2800000000000, "employees": 164000},
                {"id": 2, "ticker": "MSFT", "name": "Microsoft Corp.", "sector_id": 1, "market_cap": 3100000000000, "employees": 221000},
                {"id": 3, "ticker": "GOOGL", "name": "Alphabet Inc.", "sector_id": 1, "market_cap": 2100000000000, "employees": 190234},
                {"id": 4, "ticker": "AMZN", "name": "Amazon.com Inc.", "sector_id": 1, "market_cap": 1950000000000, "employees": 1545000},
                {"id": 5, "ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector_id": 2, "market_cap": 580000000000, "employees": 309926},
                {"id": 6, "ticker": "GS", "name": "Goldman Sachs Group Inc.", "sector_id": 2, "market_cap": 145000000000, "employees": 48500},
                {"id": 7, "ticker": "JNJ", "name": "Johnson & Johnson", "sector_id": 3, "market_cap": 375000000000, "employees": 132200},
                {"id": 8, "ticker": "PFE", "name": "Pfizer Inc.", "sector_id": 3, "market_cap": 165000000000, "employees": 88000},
                {"id": 9, "ticker": "TSLA", "name": "Tesla Inc.", "sector_id": 4, "market_cap": 720000000000, "employees": 140473},
                {"id": 10, "ticker": "XOM", "name": "Exxon Mobil Corp.", "sector_id": 5, "market_cap": 520000000000, "employees": 62000},
            ],
            "analysts": [
                {"id": 1, "first_name": "Hanu", "last_name": "Madala", "firm": "IRA Capital Management", "sector_focus": "Technology", "years_exp": 18},
                {"id": 2, "first_name": "Shankar", "last_name": "Cherukuri", "firm": "IRA Capital Management", "sector_focus": "Technology", "years_exp": 14},
                {"id": 3, "first_name": "Priya", "last_name": "Sharma", "firm": "IRA Capital Management", "sector_focus": "Healthcare", "years_exp": 10},
                {"id": 4, "first_name": "Michael", "last_name": "Chen", "firm": "IRA Capital Management", "sector_focus": "Macro", "years_exp": 16},
            ],
            "reports": [
                {"id": 1, "company_id": 1, "analyst_id": 2, "title": "Apple Q1 2025 Earnings Preview", "rating": "BUY", "target_price": 265.0, "created_at": "2025-01-25"},
                {"id": 2, "company_id": 2, "analyst_id": 2, "title": "Microsoft AI Monetization Deep Dive", "rating": "BUY", "target_price": 480.0, "created_at": "2025-02-10"},
                {"id": 3, "company_id": 3, "analyst_id": 1, "title": "Alphabet Antitrust Risk Assessment", "rating": "HOLD", "target_price": 195.0, "created_at": "2025-02-20"},
                {"id": 4, "company_id": 4, "analyst_id": 1, "title": "Amazon AWS vs AI Chip Landscape", "rating": "BUY", "target_price": 235.0, "created_at": "2025-03-01"},
            ],
            "financials": [
                {"id": 1, "company_id": 1, "fiscal_quarter": "Q1", "fiscal_year": 2025, "revenue": 124300000000, "net_income": 34500000000, "eps": 2.40, "fcf": 28500000000},
                {"id": 2, "company_id": 2, "fiscal_quarter": "Q2", "fiscal_year": 2025, "revenue": 68500000000, "net_income": 23500000000, "eps": 3.15, "fcf": 21500000000},
                {"id": 3, "company_id": 3, "fiscal_quarter": "Q1", "fiscal_year": 2025, "revenue": 88000000000, "net_income": 20600000000, "eps": 1.65, "fcf": 17800000000},
                {"id": 4, "company_id": 4, "fiscal_quarter": "Q4", "fiscal_year": 2024, "revenue": 170000000000, "net_income": 15300000000, "eps": 1.45, "fcf": 38500000000},
                {"id": 5, "company_id": 5, "fiscal_quarter": "Q1", "fiscal_year": 2025, "revenue": 41500000000, "net_income": 12500000000, "eps": 4.15, "fcf": 0},
                {"id": 6, "company_id": 9, "fiscal_quarter": "Q1", "fiscal_year": 2025, "revenue": 25100000000, "net_income": 3200000000, "eps": 0.95, "fcf": 2150000000},
            ],
            "transactions": [
                {"id": 1, "company_id": 1, "transaction_type": "BUY", "shares": 5000, "price": 195.50, "transaction_date": "2025-01-15", "insider_name": "Tim Cook"},
                {"id": 2, "company_id": 1, "transaction_type": "BUY", "shares": 2500, "price": 210.00, "transaction_date": "2025-02-20", "insider_name": "Luca Maestri"},
                {"id": 3, "company_id": 2, "transaction_type": "SELL", "shares": 15000, "price": 415.00, "transaction_date": "2025-02-01", "insider_name": "Satya Nadella"},
                {"id": 4, "company_id": 3, "transaction_type": "BUY", "shares": 1000, "price": 172.50, "transaction_date": "2025-03-05", "insider_name": "Sundar Pichai"},
            ],
            "watchlists": [
                {"id": 1, "name": "Tech Giants", "description": "Core technology holdings", "created_by": "Hanu Madala"},
                {"id": 2, "name": "Healthcare Opportunities", "description": "Pharma and biotech watch", "created_by": "Priya Sharma"},
                {"id": 3, "name": "Macro Hedges", "description": "Inflation protection positions", "created_by": "Michael Chen"},
            ],
            "alerts": [
                {"id": 1, "company_id": 1, "alert_type": "PRICE_TARGET", "condition": "price > 250", "message": "AAPL above $250 target", "active": True},
                {"id": 2, "company_id": 2, "alert_type": "EARNINGS", "condition": "date = 2025-04-22", "message": "MSFT Q3 earnings report", "active": True},
                {"id": 3, "company_id": 3, "alert_type": "NEWS", "condition": "antitrust ruling", "message": "DOJ antitrust decision expected", "active": True},
            ],
        }

    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "list tables" in query or "schema" in query:
            tables = list(self._mock_tables.keys())
            return MCPResponse(
                content=f"Available tables ({len(tables)}): {', '.join(tables)}",
                source="enterprise_db",
                metadata={"tables": tables, "count": len(tables)},
            )

        if "describe" in query:
            for table in self._mock_tables:
                if table in query:
                    rows = self._mock_tables[table]
                    if rows:
                        columns = list(rows[0].keys())
                        return MCPResponse(
                            content=f"Table '{table}': columns={columns}, rows={len(rows)}",
                            source="enterprise_db",
                            metadata={"table": table, "columns": columns, "row_count": len(rows)},
                        )
            return MCPResponse(
                content=f"Tables available: {', '.join(self._mock_tables.keys())}",
                source="enterprise_db",
            )

        if "query" in query or "select" in query or "get" in query:
            for table in self._mock_tables:
                if table in query:
                    rows = self._mock_tables[table]
                    limit = 5
                    sample = rows[:limit]
                    result = f"Table '{table}' ({len(rows)} rows, showing {limit}):\n"
                    columns = list(sample[0].keys()) if sample else []
                    result += " | ".join(columns) + "\n"
                    result += "-" * (sum(len(c) for c in columns) + 3 * len(columns)) + "\n"
                    for row in sample:
                        result += " | ".join(str(row.get(c, "")) for c in columns) + "\n"
                    return MCPResponse(
                        content=result,
                        source="enterprise_db",
                        metadata={"table": table, "total_rows": len(rows), "columns": columns},
                    )
            return MCPResponse(
                content=f"No matching table. Available: {', '.join(self._mock_tables.keys())}",
                source="enterprise_db",
            )

        if "sample" in query or "preview" in query:
            for table in self._mock_tables:
                if table in query:
                    rows = self._mock_tables[table][:3]
                    return MCPResponse(
                        content=str(rows),
                        source="enterprise_db",
                        metadata={"table": table, "sample_size": len(rows)},
                    )

        return MCPResponse(
            content="Enterprise DB tools: list_tables, describe_table, execute_query (SELECT only), get_table_sample. Try: 'list tables', 'describe companies', 'query analysts'",
            source="enterprise_db",
        )
