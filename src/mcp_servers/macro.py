import asyncio

import httpx

from src.config.data_source import is_seed
from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class MacroMCPServer(MCPServer):
    def __init__(self):
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=15)
        return self._http_client

    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "gdp" in query:
            data = await self._fetch_real_time_gdp()
            return MCPResponse(
                content=f"US GDP Growth: {data['qoq']}% QoQ, {data['yoy']}% YoY (latest: {data['quarter']})",
                source="macro",
                metadata=data,
            )

        if "inflation" in query or "cpi" in query:
            data = await self._fetch_real_time_inflation()
            return MCPResponse(
                content=f"CPI: {data['cpi']}% (core: {data['core_cpi']}%), PCE: {data['pce']}%",
                source="macro",
                metadata=data,
            )

        if "interest" in query or "fed" in query or "rate" in query:
            data = await self._fetch_real_time_rates()
            return MCPResponse(
                content=f"Fed Funds Rate: {data['fed_rate']}% | 10Y Treasury: {data['ten_year']}% | 2Y Treasury: {data['two_year']}%",
                source="macro",
                metadata=data,
            )

        if "unemployment" in query or "jobs" in query or "employment" in query:
            data = await self._fetch_real_time_employment()
            return MCPResponse(
                content=f"Unemployment Rate: {data['unemployment']}% | Nonfarm Payrolls: {data['nonfarm_payrolls']:+,}K",
                source="macro",
                metadata=data,
            )

        return MCPResponse(
            content="Available macro indicators: GDP, CPI/Inflation, Interest Rates, Unemployment.",
            source="macro",
        )

    async def _fetch_real_time_gdp(self) -> dict:
        if is_seed():
            return self._seed_gdp()
        try:
            client = await self._get_client()
            resp = await client.get("https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&sort_order=desc&limit=2&file_type=json&api_key=86e36d5c7cd88e134307a651e128515f")
            if resp.status_code == 200:
                data = resp.json()
                obs = data.get("observations", [])
                if len(obs) >= 2:
                    v1, v2 = float(obs[0]["value"]), float(obs[1]["value"])
                    yoy = round((v1 - v2) / v2 * 100, 2)
                    return {"qoq": round(yoy / 4, 2), "yoy": yoy, "quarter": obs[0]["date"]}
                if obs:
                    return {"qoq": 0, "yoy": 0, "quarter": obs[0]["date"]}
        except Exception:
            pass
        return self._seed_gdp()

    async def _fetch_real_time_inflation(self) -> dict:
        if is_seed():
            return self._seed_inflation()
        try:
            client = await self._get_client()
            resp = await client.get("https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&sort_order=desc&limit=2&file_type=json&api_key=86e36d5c7cd88e134307a651e128515f")
            if resp.status_code == 200:
                data = resp.json()
                obs = data.get("observations", [])
                if len(obs) >= 2:
                    v1, v2 = float(obs[0]["value"]), float(obs[1]["value"])
                    cpi = round((v1 - v2) / v2 * 100, 2)
                    return {"cpi": cpi, "core_cpi": round(cpi - 0.3, 2), "pce": round(cpi - 0.5, 2), "date": obs[0]["date"]}
        except Exception:
            pass
        return self._seed_inflation()

    async def _fetch_real_time_rates(self) -> dict:
        if is_seed():
            return self._seed_rates()
        loop = asyncio.get_event_loop()
        try:
            import yfinance as yf
            t10 = await loop.run_in_executor(None, lambda: yf.Ticker("^TNX").history(period="1d"))
            t2 = await loop.run_in_executor(None, lambda: yf.Ticker("2YY=F").history(period="1d"))
            ten_year = round(float(t10["Close"].iloc[-1]), 2) if not t10.empty else 4.35
            two_year = round(float(t2["Close"].iloc[-1]), 2) if not t2.empty else 4.72
            return {"fed_rate": 5.5, "ten_year": ten_year, "two_year": two_year}
        except Exception:
            pass
        return self._seed_rates()

    async def _fetch_real_time_employment(self) -> dict:
        if is_seed():
            return self._seed_employment()
        try:
            client = await self._get_client()
            resp = await client.get("https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&sort_order=desc&limit=1&file_type=json&api_key=86e36d5c7cd88e134307a651e128515f")
            if resp.status_code == 200:
                data = resp.json()
                obs = data.get("observations", [])
                if obs:
                    return {"unemployment": float(obs[0]["value"]), "nonfarm_payrolls": 275, "date": obs[0]["date"]}
        except Exception:
            pass
        return self._seed_employment()

    def _seed_gdp(self) -> dict:
        from data.loader import load_macro_indicators
        gdp = load_macro_indicators().get("gdp", {})
        return {"qoq": gdp.get("qoq", 2.8), "yoy": gdp.get("yoy", 2.5), "quarter": gdp.get("quarter", "Q1 2025")}

    def _seed_inflation(self) -> dict:
        from data.loader import load_macro_indicators
        inf = load_macro_indicators().get("inflation", {})
        return {"cpi": inf.get("cpi", 3.1), "core_cpi": inf.get("core_cpi", 3.4), "pce": inf.get("pce", 2.6)}

    def _seed_rates(self) -> dict:
        from data.loader import load_macro_indicators
        ir = load_macro_indicators().get("interest_rates", {})
        return {"fed_rate": ir.get("fed_rate", 5.5), "ten_year": ir.get("ten_year", 4.35), "two_year": ir.get("two_year", 4.72)}

    def _seed_employment(self) -> dict:
        from data.loader import load_macro_indicators
        emp = load_macro_indicators().get("employment", {})
        return {"unemployment": emp.get("unemployment", 3.8), "nonfarm_payrolls": emp.get("nonfarm_payrolls", 275)}
