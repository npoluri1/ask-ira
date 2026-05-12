import pytest

from src.mcp_servers.base import MCPRequest
from src.mcp_servers.registry import MCPRegistry, create_app


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


@pytest.mark.asyncio
async def test_enterprise_db_list_tables(registry):
    server = registry.get_server("enterprise_db")
    assert server is not None

    req = MCPRequest(query="list tables", context=None)
    result = await server.handle(req)
    assert "companies" in result.content
    assert "analysts" in result.content
    assert "sectors" in result.content
    assert "financials" in result.content


@pytest.mark.asyncio
async def test_enterprise_db_describe_table(registry):
    server = registry.get_server("enterprise_db")
    req = MCPRequest(query="describe companies", context=None)
    result = await server.handle(req)
    assert "companies" in result.content
    assert "columns" in result.content or "ticker" in result.content
    assert "row_count" in result.metadata or "columns" in result.metadata


@pytest.mark.asyncio
async def test_enterprise_db_query_table(registry):
    server = registry.get_server("enterprise_db")
    req = MCPRequest(query="query companies", context=None)
    result = await server.handle(req)
    assert "AAPL" in result.content
    assert "MSFT" in result.content


@pytest.mark.asyncio
async def test_enterprise_db_sample(registry):
    server = registry.get_server("enterprise_db")
    req = MCPRequest(query="sample financials", context=None)
    result = await server.handle(req)
    assert "revenue" in result.content.lower() or "net_income" in result.content.lower()


@pytest.mark.asyncio
async def test_enterprise_db_unknown_query(registry):
    server = registry.get_server("enterprise_db")
    req = MCPRequest(query="do something random", context=None)
    result = await server.handle(req)
    assert "Enterprise DB tools" in result.content or "list tables" in result.content.lower()


def test_create_app():
    app = create_app()
    assert app.title == "Ask IRA MCP Servers"
