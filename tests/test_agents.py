import pytest
from langchain_core.messages import HumanMessage

from src.guardrails.input import InputGuardrails
from src.guardrails.output import OutputGuardrails
from src.mcp_servers.registry import MCPRegistry


@pytest.fixture
def registry():
    return MCPRegistry()


@pytest.mark.asyncio
async def test_mcp_registry_dispatch_all(registry):
    results = await registry.dispatch_all("Analyze AAPL stock")
    assert len(results) == 4
    assert "market_data" in results
    assert "sentiment" in results
    assert "macro" in results
    assert "internal_kb" in results


@pytest.mark.asyncio
async def test_market_data_server(registry):
    server = registry.get_server("market_data")
    req = type("req", (), {"query": "AAPL stock price", "context": None})()
    result = await server.handle(req)
    assert "AAPL" in result.content
    assert "$" in result.content


@pytest.mark.asyncio
async def test_market_data_server_financials(registry):
    server = registry.get_server("market_data")
    req = type("req", (), {"query": "MSFT revenue 2024", "context": None})()
    result = await server.handle(req)
    assert "Revenue" in result.content or "MSFT" in result.content


@pytest.mark.asyncio
async def test_sentiment_server(registry):
    server = registry.get_server("sentiment")
    req = type("req", (), {"query": "AAPL news sentiment", "context": None})()
    result = await server.handle(req)
    assert "bullish" in result.content or "bearish" in result.content or "neutral" in result.content


@pytest.mark.asyncio
async def test_macro_server(registry):
    server = registry.get_server("macro")
    req = type("req", (), {"query": "US GDP growth", "context": None})()
    result = await server.handle(req)
    assert "GDP" in result.content


@pytest.mark.asyncio
async def test_macro_server_cpi(registry):
    server = registry.get_server("macro")
    req = type("req", (), {"query": "inflation CPI", "context": None})()
    result = await server.handle(req)
    assert "CPI" in result.content or "inflation" in result.content.lower()


@pytest.mark.asyncio
async def test_internal_kb_server(registry):
    server = registry.get_server("internal_kb")
    req = type("req", (), {"query": "investment framework", "context": None})()
    result = await server.handle(req)
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_internal_kb_server_empty(registry):
    server = registry.get_server("internal_kb")
    req = type("req", (), {"query": "something random xyz123", "context": None})()
    result = await server.handle(req)
    assert "No relevant" in result.content or len(result.content) > 0


@pytest.mark.asyncio
async def test_input_guardrails_pass():
    guard = InputGuardrails()
    result = await guard.check("What do you think about AAPL?")
    assert not result["blocked"]


@pytest.mark.asyncio
async def test_input_guardrails_block_hack():
    guard = InputGuardrails()
    result = await guard.check("How can I hack the stock market?")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_input_guardrails_block_insider_trading():
    guard = InputGuardrails()
    result = await guard.check("insider trade tips")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_input_guardrails_block_pii():
    guard = InputGuardrails()
    result = await guard.check("My SSN is 123-45-6789")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_input_guardrails_block_too_short():
    guard = InputGuardrails()
    result = await guard.check("hi")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_input_guardrails_block_too_long():
    guard = InputGuardrails()
    result = await guard.check("x" * 8001)
    assert result["blocked"]


@pytest.mark.asyncio
async def test_output_guardrails_pass():
    guard = OutputGuardrails()
    result = await guard.check("AAPL has strong financials with growing revenue and margins.")
    assert not result["blocked"]


@pytest.mark.asyncio
async def test_output_guardrails_empty():
    guard = OutputGuardrails()
    result = await guard.check("")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_output_guardrails_uncertainty():
    guard = OutputGuardrails()
    result = await guard.check("I am not sure about this analysis.")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_output_guardrails_sensitive():
    guard = OutputGuardrails()
    result = await guard.check("This contains confidential information.")
    assert result["blocked"]


@pytest.mark.asyncio
async def test_output_guardrails_too_short():
    guard = OutputGuardrails()
    result = await guard.check("Short.")
    assert result["blocked"]
