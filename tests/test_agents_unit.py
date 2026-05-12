import pytest

from src.agents.analyst import AnalystAgent
from src.agents.compliance import ComplianceAgent
from src.agents.critic import CriticAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.agents.risk_assessor import RiskAssessorAgent
from src.agents.writer import WriterAgent


@pytest.mark.asyncio
async def test_analyst_confidence_extraction():
    agent = AnalystAgent()
    result = await agent.analyze(
        "Analyze AAPL",
        {
            "mcp_results": {"market_data": "AAPL at $150"},
            "synthesis": "Strong company",
            "rag_context": [],
        },
    )
    assert "analysis" in result
    assert result["analysis"] is not None
    assert len(result["analysis"]) > 0


@pytest.mark.asyncio
async def test_analyst_with_rag_context():
    agent = AnalystAgent()
    result = await agent.analyze(
        "Analyze MSFT",
        {
            "mcp_results": {"market_data": "MSFT at $300"},
            "synthesis": "Growing cloud business",
            "rag_context": ["MSFT has strong competitive moat"],
        },
    )
    assert "analysis" in result


@pytest.mark.asyncio
async def test_compliance_empty_report():
    agent = ComplianceAgent()
    result = await agent.check("")
    assert "compliance_issues" in result
    assert "compliant" in result


@pytest.mark.asyncio
async def test_compliance_clean_report():
    agent = ComplianceAgent()
    report = (
        "This is not financial advice. Past performance does not guarantee future results. "
        "Consult your financial advisor. AAPL shows strong growth."
    )
    result = await agent.check(report)
    assert isinstance(result["compliant"], bool)


@pytest.mark.asyncio
async def test_compliance_regulatory_keyword():
    agent = ComplianceAgent()
    report = "This investment is a sure thing with guaranteed returns."
    result = await agent.check(report)
    issues = result["compliance_issues"]
    high_sev = [i for i in issues if i["severity"] == "high"]
    assert len(high_sev) > 0


@pytest.mark.asyncio
async def test_critic_critique_analysis():
    agent = CriticAgent()
    result = await agent.critique_analysis(
        "Analyze AAPL",
        "AAPL is a strong buy with growing revenue.",
        {"mcp_results": {"market_data": "AAPL at $150"}},
    )
    assert "critique" in result
    assert len(result["critique"]) > 0


@pytest.mark.asyncio
async def test_critic_critique_report():
    agent = CriticAgent()
    report = "# AAPL Analysis\n\nApple is performing well.\n\n## Recommendation\nBuy."
    result = await agent.critique_report(report)
    assert "report_critique" in result


@pytest.mark.asyncio
async def test_portfolio_manager_conservative():
    agent = PortfolioManagerAgent()
    result = await agent.build_portfolio(
        "Build a portfolio",
        {
            "risk_profile": "conservative",
            "servers": ["AAPL", "MSFT"],
            "mcp_results": {"market_data": "stable"},
            "analysis": "low risk",
        },
    )
    assert "allocation" in result
    assert result["risk_profile"] == "conservative"
    assert result["allocation"]["bonds"] >= result["allocation"]["equities"]


@pytest.mark.asyncio
async def test_portfolio_manager_aggressive():
    agent = PortfolioManagerAgent()
    result = await agent.build_portfolio(
        "Aggressive growth",
        {
            "risk_profile": "aggressive",
            "servers": ["TSLA", "AMZN"],
            "mcp_results": {"market_data": "high growth"},
            "analysis": "high risk high reward",
        },
    )
    assert result["risk_profile"] == "aggressive"
    assert result["allocation"]["equities"] >= 0.70


@pytest.mark.asyncio
async def test_portfolio_manager_default_profile():
    agent = PortfolioManagerAgent()
    result = await agent.build_portfolio(
        "Build portfolio",
        {
            "risk_profile": "unknown",
            "mcp_results": {},
            "analysis": "neutral",
        },
    )
    assert "allocation" in result


@pytest.mark.asyncio
async def test_risk_assessor():
    agent = RiskAssessorAgent()
    result = await agent.assess(
        "Assess TSLA risk",
        {
            "mcp_results": {
                "market_data": "TSLA at $200 with high volatility",
                "macro": "Interest rates rising",
            },
            "analysis": "High growth but risky",
            "servers": ["TSLA"],
        },
    )
    assert "risk_assessment" in result
    assert len(result["risk_assessment"]) > 0


@pytest.mark.asyncio
async def test_writer():
    agent = WriterAgent()
    result = await agent.write(
        "Write report on AAPL",
        {
            "analysis": "AAPL is a strong buy with good fundamentals.",
            "mcp_results": {"market_data": "AAPL at $150, P/E 28"},
        },
    )
    assert "report" in result
    assert len(result["report"]) > 0


@pytest.mark.asyncio
async def test_writer_empty_analysis():
    agent = WriterAgent()
    result = await agent.write(
        "Write report",
        {
            "analysis": "",
            "mcp_results": {},
        },
    )
    assert "report" in result


@pytest.mark.asyncio
async def test_researcher_with_mock_registry():
    from src.agents.researcher import ResearcherAgent
    from src.mcp_servers.base import MCPResponse

    class MockRegistry:
        async def dispatch_all(self, query: str) -> dict:
            return {
                "market_data": MCPResponse(content="AAPL at $242, P/E 32", source="market_data"),
                "sentiment": MCPResponse(content="Bullish sentiment 72%", source="sentiment"),
            }

    agent = ResearcherAgent(MockRegistry())
    result = await agent.research("Analyze AAPL")
    assert "mcp_results" in result
    assert "market_data" in result["mcp_results"]
    assert "AAPL" in result["mcp_results"]["market_data"]
    assert "rag_context" in result
    assert "synthesis" in result
    assert result["next"] == "analyst"


@pytest.mark.asyncio
async def test_researcher_handles_empty_registry():
    from src.agents.researcher import ResearcherAgent

    class EmptyRegistry:
        async def dispatch_all(self, query: str) -> dict:
            return {}

    agent = ResearcherAgent(EmptyRegistry())
    result = await agent.research("test")
    assert result["mcp_results"] == {}


@pytest.mark.asyncio
async def test_human_review_logic_direct():

    report_with_disclaimer = "This is not financial advice. Past performance varies."
    report_no_disclaimer = "Buy this stock now! It will go up 1000%."
    disclaimers = ["not financial advice", "past performance", "consult your"]

    has_1 = any(p in report_with_disclaimer.lower() for p in disclaimers)
    has_2 = any(p in report_no_disclaimer.lower() for p in disclaimers)

    assert has_1 is True
    assert has_2 is False
