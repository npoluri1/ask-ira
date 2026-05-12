import asyncio

import yfinance as yf

from src.config.data_source import is_seed, is_realtime
from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class MarketDataMCPServer(MCPServer):
    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "price" in query or "stock" in query or "quote" in query:
            ticker = self._extract_ticker(query)
            price_data = await self._fetch_stock_price(ticker)
            return MCPResponse(
                content=(
                    f"{ticker}: ${price_data['price']:.2f} "
                    f"({price_data['change']:+.2f}, {price_data['change_pct']:+.2f}%) "
                    f"| Day Range: ${price_data['low']:.2f} - ${price_data['high']:.2f}"
                    f" | Vol: {price_data['volume']:,}"
                ),
                source="market_data",
                metadata={"ticker": ticker, **price_data},
            )

        if "financials" in query or "income" in query or "revenue" in query:
            ticker = self._extract_ticker(query)
            financials = await self._fetch_financials(ticker)
            return MCPResponse(
                content=(
                    f"Revenue (TTM): ${financials['revenue']:,.0f}, "
                    f"Net Income: ${financials['net_income']:,.0f}, "
                    f"EPS (TTM): ${financials['eps']:.2f}, "
                    f"P/E: {financials['pe_ratio']:.1f}, "
                    f"Market Cap: ${financials['market_cap']:,.0f}"
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

    async def _fetch_stock_price(self, ticker: str) -> dict:
        if is_seed():
            return self._seed_stock_price(ticker)
        loop = asyncio.get_event_loop()
        try:
            t = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            info = await loop.run_in_executor(None, lambda: t.info or {})
            hist = await loop.run_in_executor(None, lambda: t.history(period="2d"))
            if not hist.empty:
                close = hist["Close"]
                price = float(close.iloc[-1])
                prev = float(close.iloc[-2]) if len(close) > 1 else price
            else:
                price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                prev = info.get("previousClose", price)
            change = price - prev
            change_pct = (change / prev * 100) if prev else 0
            return {
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "high": round(float(hist["High"].max()) if not hist.empty else (info.get("dayHigh") or price), 2),
                "low": round(float(hist["Low"].min()) if not hist.empty else (info.get("dayLow") or price), 2),
                "volume": int(hist["Volume"].iloc[-1]) if not hist.empty else info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "name": info.get("shortName") or info.get("longName") or ticker,
            }
        except Exception:
            return self._seed_stock_price(ticker)

    async def _fetch_financials(self, ticker: str) -> dict:
        if is_seed():
            return self._seed_financials(ticker)
        loop = asyncio.get_event_loop()
        try:
            t = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            info = await loop.run_in_executor(None, lambda: t.info or {})
            return {
                "revenue": info.get("totalRevenue") or info.get("revenue", 0),
                "net_income": info.get("netIncomeToCommon", 0),
                "eps": info.get("trailingEps") or info.get("forwardEps", 0),
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE", 0),
                "market_cap": info.get("marketCap", 0),
            }
        except Exception:
            return self._seed_financials(ticker)

    async def _fetch_sec_filings(self, ticker: str) -> list[dict]:
        from data.loader import load_sec_filings
        result = load_sec_filings(ticker)
        if result:
            return result[0].get("filings", [])
        return []

    def _seed_stock_price(self, ticker: str) -> dict:
        from data.loader import load_financial_metrics_for_ticker
        result = load_financial_metrics_for_ticker(ticker)
        if result:
            return {
                "price": result.get("current_price", 150),
                "change": result.get("daily_change", 0),
                "change_pct": result.get("daily_change_pct", 0),
                "high": result.get("high", 155),
                "low": result.get("low", 148),
                "volume": result.get("volume", 50000000),
                "market_cap": result.get("market_cap", 0),
                "name": result.get("name", ticker),
            }
        return {"price": 150, "change": 0, "change_pct": 0, "high": 155, "low": 148, "volume": 50000000, "market_cap": 0, "name": ticker}

    def _seed_financials(self, ticker: str) -> dict:
        from data.loader import load_financial_metrics_for_ticker
        result = load_financial_metrics_for_ticker(ticker)
        if result:
            return {
                "revenue": result.get("revenue", 0),
                "net_income": result.get("net_income", 0),
                "eps": result.get("eps", 0),
                "pe_ratio": result.get("pe_ratio", 0),
                "market_cap": result.get("market_cap", 0),
            }
        return {"revenue": 0, "net_income": 0, "eps": 0.0, "pe_ratio": 0.0, "market_cap": 0}
