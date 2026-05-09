from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.analyst import AnalystAgent
from src.agents.compliance import ComplianceAgent
from src.agents.critic import CriticAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.agents.researcher import ResearcherAgent
from src.agents.risk_assessor import RiskAssessorAgent
from src.agents.state import AgentState
from src.agents.supervisor import SupervisorAgent
from src.agents.writer import WriterAgent
from src.config import get_settings
from src.guardrails.input import InputGuardrails
from src.guardrails.output import OutputGuardrails
from src.mcp_servers.registry import MCPRegistry

settings = get_settings()


def create_graph(
    mcp_registry: MCPRegistry | None = None,
    memory: bool = True,
    enable_human_review: bool = False,
) -> StateGraph:
    registry = mcp_registry or MCPRegistry()
    supervisor = SupervisorAgent(registry)
    researcher = ResearcherAgent(registry)
    analyst = AnalystAgent()
    writer = WriterAgent()
    critic = CriticAgent()
    portfolio_manager = PortfolioManagerAgent()
    risk_assessor = RiskAssessorAgent()
    compliance = ComplianceAgent()
    input_guard = InputGuardrails()
    output_guard = OutputGuardrails()

    builder = StateGraph(AgentState)

    async def guard_input(state: AgentState) -> dict:
        result = await input_guard.check(state["query"])
        if result["blocked"]:
            return {
                "messages": [HumanMessage(content=f"[BLOCKED] {result['reason']}")],
                "next": END,
            }
        return {"next": "supervisor"}

    async def route_supervisor(state: AgentState) -> dict:
        plan = await supervisor.plan(state["query"])
        return {
            "plan": plan["plan"],
            "dimensions": plan.get("dimensions", []),
            "servers": plan.get("servers", []),
            "use_rag": plan.get("use_rag", True),
            "mcp_results": {},
            "rag_context": [],
            "risk_profile": plan.get("risk_profile", "moderate"),
            "next": plan["next"],
        }

    async def research_and_rag(state: AgentState) -> dict:
        results = await researcher.research(state["query"])
        return {
            "mcp_results": results["mcp_results"],
            "rag_context": results.get("rag_context", []),
            "synthesis": results.get("synthesis", ""),
            "next": results["next"],
        }

    async def analyze(state: AgentState) -> dict:
        result = await analyst.analyze(state["query"], dict(state))
        return {
            "analysis": result["analysis"],
            "confidence": result.get("confidence"),
            "next": "critic_analysis",
        }

    async def critique_analysis(state: AgentState) -> dict:
        critique = await critic.critique_analysis(
            state["query"], state.get("analysis", ""), dict(state)
        )
        iteration = state.get("iteration", 0)

        if iteration < critic.max_iterations:
            return {
                "critique": critique["critique"],
                "iteration": iteration + 1,
            }
        return {
            "critique": critique["critique"],
            "next": "portfolio_manager",
        }

    async def assess_risk(state: AgentState) -> dict:
        result = await risk_assessor.assess(state["query"], dict(state))
        return {
            "risk_assessment": result["risk_assessment"],
            "next": "compliance",
        }

    async def run_compliance(state: AgentState) -> dict:
        report = state.get("report", "")
        result = await compliance.check(report)
        return {
            "compliance_result": result,
            "next": "human_review" if (enable_human_review and settings.enable_human_review) else "guard_output",
        }

    async def build_portfolio(state: AgentState) -> dict:
        result = await portfolio_manager.build_portfolio(state["query"], dict(state))
        return {
            "portfolio_allocation": result,
            "next": "risk_assessor",
        }

    async def write_report(state: AgentState) -> dict:
        result = await writer.write(state["query"], dict(state))
        return {"report": result["report"], "next": "critic_report"}

    async def critique_report(state: AgentState) -> dict:
        critique = await critic.critique_report(state.get("report", ""))
        return {
            "critique": critique["report_critique"],
            "next": "compliance",
        }

    async def guard_output(state: AgentState) -> dict:
        if not state.get("report"):
            return {"next": END}
        result = await output_guard.check(state["report"])
        if result["blocked"]:
            return {
                "report": f"[WARNING: {result['reason']}]\n\n{state['report']}",
                "next": END,
            }
        return {"next": END}

    async def human_review(state: AgentState) -> dict:
        report = state.get("report", "")
        has_disclaimer = any(
            phrase in report.lower()
            for phrase in ["not financial advice", "past performance", "consult your"]
        )
        return {"human_approved": has_disclaimer, "next": "guard_output"}

    builder.add_node("guard_input", guard_input)
    builder.add_node("supervisor", route_supervisor)
    builder.add_node("researcher", research_and_rag)
    builder.add_node("analyst", analyze)
    builder.add_node("critic_analysis", critique_analysis)
    builder.add_node("portfolio_manager", build_portfolio)
    builder.add_node("risk_assessor", assess_risk)
    builder.add_node("writer", write_report)
    builder.add_node("critic_report", critique_report)
    builder.add_node("compliance", run_compliance)
    builder.add_node("human_review", human_review)
    builder.add_node("guard_output", guard_output)

    builder.add_edge(START, "guard_input")
    builder.add_conditional_edges("guard_input", lambda s: s.get("next", END))

    builder.add_edge("supervisor", "researcher")
    builder.add_edge("researcher", "analyst")
    builder.add_edge("analyst", "critic_analysis")

    builder.add_conditional_edges(
        "critic_analysis",
        lambda s: "analyst" if (
            s.get("critique") and s.get("iteration", 0) < critic.max_iterations
        ) else "portfolio_manager",
    )

    builder.add_edge("portfolio_manager", "risk_assessor")
    builder.add_edge("risk_assessor", "writer")
    builder.add_edge("writer", "critic_report")
    builder.add_edge("critic_report", "compliance")

    builder.add_conditional_edges(
        "compliance",
        lambda s: s.get("next", "guard_output"),
    )
    builder.add_conditional_edges(
        "human_review",
        lambda s: "guard_output" if s.get("human_approved") else "writer",
    )

    builder.add_edge("guard_output", END)

    checkpointer = MemorySaver() if memory else None
    return builder.compile(checkpointer=checkpointer)


async def run_ira(query: str, graph=None, enable_human_review: bool = False) -> dict:
    from src.mcp_servers.registry import MCPRegistry

    g = graph or create_graph(MCPRegistry(), enable_human_review=enable_human_review)
    config = {"configurable": {"thread_id": "ira-session-1"}}
    result = await g.ainvoke(
        {
            "query": query,
            "messages": [HumanMessage(content=query)],
            "iteration": 0,
            "risk_profile": "moderate",
            "portfolio_allocation": None,
            "risk_assessment": None,
            "critique": None,
            "compliance_result": None,
            "human_approved": None,
        },
        config,
    )
    return result
