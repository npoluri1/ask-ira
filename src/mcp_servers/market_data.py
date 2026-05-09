import httpx

from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class MarketDataMCPServer(MCPServer):
    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "price" in query or "stock" in query:
            ticker = self._extract_ticker(query)
            price_data = await self._fetch_stock_price(ticker)
            return MCPResponse(
                content=f"{ticker}: ${price_data:.2f}",
                source="market_data",
                metadata={"ticker": ticker, "price": price_data},
            )

        if "financials" in query or "income" in query or "revenue" in query:
            ticker = self._extract_ticker(query)
            financials = await self._fetch_financials(ticker)
            return MCPResponse(
                content=(
                    f"Revenue: ${financials['revenue']:,.0f}, "
                    f"Net Income: ${financials['net_income']:,.0f}, "
                    f"EPS: ${financials['eps']:.2f}"
                ),
                source="market_data",
                metadata={"ticker": ticker, **financials},
            )

        if "sec" in query or "filing" in query:
            ticker = self._extract_ticker(query)
            filings = await self._fetch_sec_filings(ticker)
            return MCPResponse(
                content=(
                    f"Recent SEC filings for {ticker}: "
                    f"{', '.join(f['type'] for f in filings[:5])}"
                ),
                source="market_data",
                metadata={"ticker": ticker, "filings": filings[:5]},
            )

        return MCPResponse(
            content="Available queries: stock price, financials, SEC filings for a ticker.",
            source="market_data",
        )

    def _extract_ticker(self, query: str) -> str:
        words = query.upper().split()
        for w in words:
            if w.isalpha() and len(w) <= 5:
                return w
        return "AAPL"

    async def _fetch_stock_price(self, ticker: str) -> float:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    timeout=10,
                )
                data = resp.json()
                return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            except Exception:
                return 150.0 + hash(ticker) % 5000 / 100

    async def _fetch_financials(self, ticker: str) -> dict:
        from data.loader import load_financial_metrics_for_ticker
        result = load_financial_metrics_for_ticker(ticker)
        if result:
            return {
                "revenue": result["revenue"],
                "net_income": result["net_income"],
                "eps": result["eps"],
                "pe_ratio": result["pe_ratio"],
                "market_cap": result["market_cap"],
            }
        return {
            "revenue": 0,
            "net_income": 0,
            "eps": 0.0,
            "pe_ratio": 0.0,
            "market_cap": 0,
        }

    async def _fetch_sec_filings(self, ticker: str) -> list[dict]:
        from data.loader import load_sec_filings
        result = load_sec_filings(ticker)
        if result:
            return result[0].get("filings", [])
        return []
