import asyncio
import time
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage

from src.api.models import QueryRequest, QueryResponse
from src.api.fallback_query import generate_fallback_report
from src.config import get_settings
from src.config.data_source import (
    get_data_source,
    get_source_badge,
    get_source_label,
    is_realtime,
    set_data_source,
    toggle_data_source,
)
from src.mcp_servers.registry import MCPRegistry
from src.streaming import manager, stream_research
from src.agents.graph import create_graph

logger = logging.getLogger("ask-ira")
settings = get_settings()
router = APIRouter(prefix="/api/v1")
config_router = APIRouter(prefix="/api/v1/config")
_graphs: dict[str, tuple[any, float]] = {}
_GRAPH_TTL = 3600


@config_router.get("/data-source")
async def get_data_source_endpoint():
    return {
        "mode": get_data_source(),
        "label": get_source_label(),
        "badge": get_source_badge(),
        "is_realtime": is_realtime(),
    }


@config_router.post("/data-source/toggle")
async def toggle_data_source_endpoint():
    new_mode = toggle_data_source()
    return {
        "mode": new_mode,
        "label": get_source_label(),
        "badge": get_source_badge(),
        "is_realtime": is_realtime(),
    }


@config_router.post("/data-source")
async def set_data_source_endpoint(mode: str):
    mode = mode.lower()
    if mode not in ("realtime", "seed"):
        return JSONResponse(status_code=400, content={"error": "Mode must be 'realtime' or 'seed'"})
    set_data_source(mode)
    return {
        "mode": get_data_source(),
        "label": get_source_label(),
        "badge": get_source_badge(),
        "is_realtime": is_realtime(),
    }


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
    try:
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
    except Exception as e:
        logger.warning("AI query failed, using fallback: %s", e)
        try:
            fallback = generate_fallback_report(request.query, request.risk_profile)
        except Exception as fbe:
            logger.error("Fallback also failed: %s", fbe)
            fallback = {"report": f"## AI Research Report\n\nUnable to generate analysis for '{request.query}'. Please try a different query.", "confidence": 0.5, "session_id": request.session_id}
        return QueryResponse(
            report=fallback.get("report", "No report generated."),
            analysis=fallback.get("analysis"),
            mcp_results=fallback.get("mcp_results"),
            portfolio_allocation=fallback.get("portfolio_allocation"),
            risk_assessment=fallback.get("risk_assessment"),
            confidence=fallback.get("confidence"),
            session_id=request.session_id,
        )


@router.get("/insights/{section}")
async def get_insights(section: str):
    topics = {
        "dashboard": "Global market overview and key trends for today with major indices performance summary",
        "stocks": "Stock market analysis and top picks for today's trading session",
        "indices": "Major index performance analysis and overall market direction for the day",
        "forex": "Foreign exchange market major pair movements and short-term outlook",
        "crypto": "Cryptocurrency market analysis, top coin movements and emerging trends",
        "commodities": "Commodity prices overview including gold, oil and supply-demand dynamics",
        "bonds": "Bond market yields analysis and fixed income investment outlook",
        "funds": "Mutual funds and ETF performance analysis with sector rotation insights",
        "economy": "Key economic indicators and macroeconomic outlook for the quarter",
    }
    query = topics.get(section, f"Market analysis for {section}")
    try:
        graph = _get_graph(f"insight-{section}")
        config = {"configurable": {"thread_id": f"insight-{section}"}}
        state = _build_initial_state(query, f"insight-{section}", "moderate")
        result = await graph.ainvoke(state, config)
        combined = result.get("report") or result.get("analysis") or ""
        return {"insight": combined[:600], "confidence": result.get("confidence", 0.7), "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S UTC")}
    except Exception as e:
        logger.warning("Insights LLM failed for %s: %s, using fallback", section, e)
        try:
            fallback = generate_fallback_report(query, "moderate")
            return {"insight": fallback.get("report", "")[:500], "confidence": fallback.get("confidence", 0.5), "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S UTC")}
        except Exception:
            return {"insight": f"AI insights temporarily unavailable for {section}.", "confidence": 0, "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S UTC")}


@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    async def event_stream():
        try:
            graph = _get_graph(request.session_id)
            config = {"configurable": {"thread_id": request.session_id}}
            
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
                    yield f"data: {{\"type\":\"status\",\"stage\":\"{name}\",\"message\":\"{stages[name]}\"}}\n\n"  # noqa: E501
                if kind == "on_chain_end" and name == "writer":
                    data = event.get("data", {}).get("output", {})
                    if isinstance(data, dict) and "report" in data:
                        safe = data["report"].replace("\n", "\\n").replace('"', '\\"')
                        yield f"data: {{\"type\":\"report_chunk\",\"content\":\"{safe}\"}}\n\n"
                await asyncio.sleep(0.01)
            yield 'data: {"type":"complete","message":"Research complete"}\n\n'
        except Exception as e:
            logger.error("Streaming error: %s", e, exc_info=True)
            yield f'data: {{"type":"error","message":"AI research failed: {str(e)}"}}\n\n'

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
