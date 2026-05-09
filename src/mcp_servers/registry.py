from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer
from src.mcp_servers.enterprise_db import EnterpriseDBMCPServer
from src.mcp_servers.internal_kb import InternalKBMCPServer
from src.mcp_servers.macro import MacroMCPServer
from src.mcp_servers.market_data import MarketDataMCPServer
from src.mcp_servers.sentiment import SentimentMCPServer


def create_app():
    from fastapi import FastAPI

    app = FastAPI(title="Ask IRA MCP Servers", version="0.2.0")

    registry = MCPRegistry()

    @app.get("/health")
    async def health():
        return {"status": "ok", "servers": registry.server_names}

    @app.post("/dispatch")
    async def dispatch(query: str):
        results = await registry.dispatch_all(query)
        return {name: resp.content for name, resp in results.items()}

    return app


class MCPRegistry:
    def __init__(self, include_enterprise_db: bool = False):
        self._servers: dict[str, MCPServer] = {
            "market_data": MarketDataMCPServer(),
            "sentiment": SentimentMCPServer(),
            "macro": MacroMCPServer(),
            "internal_kb": InternalKBMCPServer(),
        }
        if include_enterprise_db:
            self._servers["enterprise_db"] = EnterpriseDBMCPServer()

    @property
    def server_names(self) -> list[str]:
        return list(self._servers.keys())

    def get_server(self, name: str) -> MCPServer | None:
        return self._servers.get(name)

    async def dispatch_all(self, query: str) -> dict[str, MCPResponse]:
        from asyncio import gather

        async def dispatch(name: str, server: MCPServer) -> tuple[str, MCPResponse]:
            result = await server.handle(MCPRequest(query=query))
            return name, result

        tasks = [dispatch(name, srv) for name, srv in self._servers.items()]
        results = await gather(*tasks)
        return dict(results)
