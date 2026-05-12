import pytest
from src.agents.supervisor import SupervisorAgent
from src.agents.researcher import ResearcherAgent
from src.agents.risk_assessor import RiskAssessorAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.mcp_servers.registry import MCPRegistry


@pytest.fixture
def registry():
    return MCPRegistry()


@pytest.mark.asyncio
async def test_supervisor_plan(registry):
    supervisor = SupervisorAgent(registry)
    result = await supervisor.plan("Analyze AAPL stock for Q2 2026")
    assert "plan" in result
    assert "next" in result
    assert "servers" in result or "dimensions" in result


@pytest.mark.asyncio
async def test_supervisor_plan_market_query(registry):
    supervisor = SupervisorAgent(registry)
    result = await supervisor.plan("What is the current price of TSLA?")
    assert result is not None


@pytest.mark.asyncio
async def test_researcher_research(registry):
    researcher = ResearcherAgent(registry)
    result = await researcher.research("Analyze MSFT")
    assert "mcp_results" in result
    assert "next" in result


@pytest.mark.asyncio
async def test_researcher_research_with_rag_context(registry):
    researcher = ResearcherAgent(registry)
    result = await researcher.research("AAPL fundamentals")
    if "rag_context" in result:
        assert isinstance(result["rag_context"], list)


@pytest.mark.asyncio
async def test_risk_assessor_assess():
    assessor = RiskAssessorAgent()
    state = {
        "mcp_results": {"market_data": "MSFT at $400"},
        "analysis": "MSFT shows strong growth potential",
        "portfolio_allocation": {
            "risk_profile": "moderate",
            "allocation": {"equity": 0.6, "bond": 0.3, "cash": 0.1},
        },
    }
    result = await assessor.assess("Assess MSFT risk", state)
    assert "risk_assessment" in result
    assert result["risk_assessment"] is not None
    assert len(result["risk_assessment"]) > 0


@pytest.mark.asyncio
async def test_portfolio_manager_build_portfolio():
    manager = PortfolioManagerAgent()
    state = {
        "analysis": "Tech stocks are overvalued. Shift to defensive.",
        "risk_profile": "conservative",
        "mcp_results": {"market_data": "SPY at $500"},
    }
    result = await manager.build_portfolio("Build a conservative portfolio", state)
    assert result is not None
    if isinstance(result, dict):
        assert "risk_profile" in result or "allocation" in result


@pytest.mark.asyncio
async def test_portfolio_manager_aggressive_profile():
    manager = PortfolioManagerAgent()
    state = {
        "analysis": "Growth stage companies show strong momentum",
        "risk_profile": "aggressive",
        "mcp_results": {},
    }
    result = await manager.build_portfolio("Aggressive growth portfolio", state)
    assert result is not None
