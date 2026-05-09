from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    query: str
    messages: Annotated[list[AnyMessage], add_messages]
    plan: str | None
    dimensions: list[str]
    servers: list[str]
    use_rag: bool
    mcp_results: dict[str, str]
    rag_context: list[str]
    analysis: str | None
    synthesis: str
    report: str | None
    confidence: float | None
    next: Literal[
        "researcher", "analyst", "writer", "portfolio_manager", "risk_assessor",
        "critic", "compliance", "guard_output", "human_review", "__end__",
    ] | None
    iteration: int

    risk_profile: str | None
    portfolio_allocation: dict | None
    risk_assessment: str | None
    critique: str | None
    compliance_result: dict | None
    human_approved: bool | None
