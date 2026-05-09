import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.agents.graph import create_graph
from src.api.models import QueryRequest, QueryResponse
from src.config import get_settings
from src.mcp_servers.registry import MCPRegistry
from src.streaming import manager, stream_research

settings = get_settings()
router = APIRouter(prefix="/api/v1")
_graphs: dict[str, tuple[any, float]] = {}
_GRAPH_TTL = 3600


def _get_graph(session_id: str):
    now = time.time()
    if session_id in _graphs:
        graph, ts = _graphs[session_id]
        if now - ts < _GRAPH_TTL:
            return graph
    stale = [sid for sid, (_, ts) in _graphs.items() if now - ts > _GRAPH_TTL]
    for sid in stale:
        del _graphs[sid]
    graph = create_graph(MCPRegistry())
    _graphs[session_id] = (graph, now)
    return graph


def _build_initial_state(query: str, session_id: str, risk_profile: str | None) -> dict:
    return {
        "query": query,
        "messages": [HumanMessage(content=query)],
        "iteration": 0,
        "risk_profile": risk_profile or "moderate",
        "portfolio_allocation": None,
        "risk_assessment": None,
        "critique": None,
        "compliance_result": None,
        "human_approved": None,
    }


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    graph = _get_graph(request.session_id)
    config = {"configurable": {"thread_id": request.session_id}}

    result = await graph.ainvoke(
        _build_initial_state(request.query, request.session_id, request.risk_profile),
        config,
    )

    return QueryResponse(
        report=result.get("report", "No report generated."),
        analysis=result.get("analysis"),
        mcp_results=result.get("mcp_results"),
        portfolio_allocation=result.get("portfolio_allocation"),
        risk_assessment=result.get("risk_assessment"),
        confidence=result.get("confidence"),
        session_id=request.session_id,
    )


@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    graph = _get_graph(request.session_id)
    config = {"configurable": {"thread_id": request.session_id}}

    async def event_stream():
        stages = {
            "guard_input": "Checking input safety...",
            "supervisor": "Planning research strategy...",
            "researcher": "Gathering data from MCP servers...",
            "analyst": "Analyzing research data...",
            "critic_analysis": "Reviewing analysis quality...",
            "portfolio_manager": "Building portfolio allocation...",
            "risk_assessor": "Assessing risk factors...",
            "writer": "Generating report...",
            "critic_report": "Reviewing report quality...",
            "compliance": "Running compliance checks...",
            "guard_output": "Final safety check...",
        }
        async for event in graph.astream_events(
            _build_initial_state(request.query, request.session_id, request.risk_profile),
            config,
            version="v2",
        ):
            kind = event.get("event", "")
            name = event.get("name", "")
            if kind == "on_chain_start" and name in stages:
                yield f"data: {{\"type\":\"status\",\"stage\":\"{name}\",\"message\":\"{stages[name]}\"}}\n\n"
            if kind == "on_chain_end" and name == "writer":
                data = event.get("data", {}).get("output", {})
                if isinstance(data, dict) and "report" in data:
                    safe = data["report"].replace("\n", "\\n").replace('"', '\\"')
                    yield f"data: {{\"type\":\"report_chunk\",\"content\":\"{safe}\"}}\n\n"
            await asyncio.sleep(0.01)
        yield 'data: {"type":"complete","message":"Research complete"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        query = data.get("query", "")
        if query:
            await stream_research(query, session_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(session_id)
