import pytest

from src.agents.graph import create_graph, run_ira
from src.agents.state import AgentState


def test_create_graph():
    graph = create_graph(memory=False)
    assert graph is not None


def test_create_graph_with_human_review():
    graph = create_graph(memory=False, enable_human_review=True)
    assert graph is not None


def test_create_graph_schema():
    graph = create_graph(memory=False)
    assert hasattr(graph, "get_graph")


def test_agent_state_fields():
    state = AgentState(
        query="test query",
        messages=[],
        plan=None,
        dimensions=[],
        servers=[],
        use_rag=False,
        mcp_results={},
        rag_context=[],
        synthesis="",
        analysis=None,
        report=None,
        confidence=None,
        next=None,
        iteration=0,
        risk_profile=None,
        portfolio_allocation=None,
        risk_assessment=None,
        critique=None,
        compliance_result=None,
        human_approved=None,
    )
    assert state["query"] == "test query"
    assert state["synthesis"] == ""
    assert state["iteration"] == 0
    assert state["next"] is None


@pytest.mark.asyncio
async def test_run_ira():
    result = await run_ira("Analyze AAPL briefly")
    assert "report" in result or "analysis" in result or "messages" in result
