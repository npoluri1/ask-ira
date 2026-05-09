import pytest

from src.mcp_servers.registry import MCPRegistry, create_app
from src.mcp_servers.base import MCPRequest


@pytest.fixture
def registry():
    return MCPRegistry(include_enterprise_db=True)


@pytest.mark.asyncio
async def test_registry_server_names(registry):
    names = registry.server_names
    assert "market_data" in names
    assert "sentiment" in names
    assert "macro" in names
    assert "internal_kb" in names
    assert "enterprise_db" in names


@pytest.mark.asyncio
async def test_registry_get_server(registry):
    server = registry.get_server("market_data")
    assert server is not None
    assert server.__class__.__name__ == "MarketDataMCPServer"


@pytest.mark.asyncio
async def test_registry_get_server_missing(registry):
    server = registry.get_server("nonexistent")
    assert server is None


@pytest.mark.asyncio
async def test_base_mcp_request():
    req = MCPRequest(query="test query", context={"key": "value"})
    assert req.query == "test query"
    assert req.context == {"key": "value"}


@pytest.mark.asyncio
async def test_base_mcp_request_defaults():
    req = MCPRequest(query="test")
    assert req.context is None


def test_create_app():
    app = create_app()
    assert app.title == "Ask IRA MCP Servers"
