from data.loader import load_macro_indicators
from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class MacroMCPServer(MCPServer):
    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "gdp" in query:
            data = await self._fetch_gdp()
            return MCPResponse(
                content=f"US GDP Growth: {data['qoq']}% QoQ, {data['yoy']}% YoY "
                        f"(latest: {data['quarter']})",
                source="macro",
                metadata=data,
            )

        if "inflation" in query or "cpi" in query:
            data = await self._fetch_inflation()
            return MCPResponse(
                content=f"CPI: {data['cpi']}% (core: {data['core_cpi']}%), PCE: {data['pce']}%",
                source="macro",
                metadata=data,
            )

        if "interest" in query or "fed" in query or "rate" in query:
            data = await self._fetch_interest_rates()
            return MCPResponse(
                content=f"Fed Funds Rate: {data['fed_rate']}% | 10Y Treasury: {data['ten_year']}% "
                        f"| 2Y Treasury: {data['two_year']}%",
                source="macro",
                metadata=data,
            )

        if "unemployment" in query or "jobs" in query or "employment" in query:
            data = await self._fetch_employment()
            return MCPResponse(
                content=f"Unemployment Rate: {data['unemployment']}% | "
                        f"Nonfarm Payrolls: {data['nonfarm_payrolls']:+,}K",
                source="macro",
                metadata=data,
            )

        return MCPResponse(
            content="Available macro indicators: GDP, CPI/Inflation, Interest Rates, Unemployment.",
            source="macro",
        )

    async def _fetch_gdp(self) -> dict:
        data = load_macro_indicators()
        gdp = data.get("gdp", {})
        return {
            "qoq": gdp.get("qoq", 2.8),
            "yoy": gdp.get("yoy", 2.5),
            "quarter": gdp.get("quarter", "Q1 2025"),
        }

    async def _fetch_inflation(self) -> dict:
        data = load_macro_indicators()
        inf = data.get("inflation", {})
        return {
            "cpi": inf.get("cpi", 3.1),
            "core_cpi": inf.get("core_cpi", 3.4),
            "pce": inf.get("pce", 2.6),
        }

    async def _fetch_interest_rates(self) -> dict:
        data = load_macro_indicators()
        ir = data.get("interest_rates", {})
        return {
            "fed_rate": ir.get("fed_rate", 5.5),
            "ten_year": ir.get("ten_year", 4.35),
            "two_year": ir.get("two_year", 4.72),
        }

    async def _fetch_employment(self) -> dict:
        data = load_macro_indicators()
        emp = data.get("employment", {})
        return {
            "unemployment": emp.get("unemployment", 3.8),
            "nonfarm_payrolls": emp.get("nonfarm_payrolls", 275),
        }
