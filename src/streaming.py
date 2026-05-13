"""WebSocket and SSE streaming for real-time research report generation."""

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from src.agents.graph import create_graph
from src.mcp_servers.registry import MCPRegistry

logger = logging.getLogger("ask-ira.streaming")


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    async def send_json(self, session_id: str, data: dict):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(session_id)

    async def broadcast(self, data: dict):
        dead = []
        for sid, ws in self._connections.items():
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(sid)
        for sid in dead:
            self.disconnect(sid)


manager = ConnectionManager()

STAGE_LABELS = {
    "guard_input": "Checking input safety...",
    "supervisor": "Planning research strategy...",
    "researcher": "Gathering data from MCP servers & RAG...",
    "analyst": "Analyzing research data...",
    "critic_analysis": "Reviewing analysis quality...",
    "portfolio_manager": "Building portfolio allocation...",
    "risk_assessor": "Assessing risk factors...",
    "writer": "Generating investment report...",
    "critic_report": "Reviewing report quality...",
    "compliance": "Running compliance checks...",
    "human_review": "Awaiting human review...",
    "guard_output": "Final safety check...",
}


async def stream_research(query: str, session_id: str, websocket: WebSocket):
    await manager.connect(session_id, websocket)

    try:
        await manager.send_json(session_id, {
            "type": "status",
            "stage": "starting",
            "message": "Initializing research pipeline...",
        })

        graph = create_graph(MCPRegistry())
        config = {"configurable": {"thread_id": session_id}}

        reported_stages = set()

        async for event in graph.astream_events(
            {
                "query": query,
                "messages": [],
                "iteration": 0,
                "risk_profile": "moderate",
                "portfolio_allocation": None,
                "risk_assessment": None,
                "critique": None,
                "compliance_result": None,
                "human_approved": None,
            },
            config,
            version="v2",
        ):
            kind = event.get("event", "")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in STAGE_LABELS and name not in reported_stages:
                reported_stages.add(name)
                await manager.send_json(session_id, {
                    "type": "status",
                    "stage": name,
                    "message": STAGE_LABELS[name],
                })

            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", None)
                if chunk and hasattr(chunk, "content") and chunk.content:
                    await manager.send_json(session_id, {
                        "type": "token",
                        "content": chunk.content,
                    })

            if kind == "on_chain_end":
                data = event.get("data", {}).get("output", {})
                if isinstance(data, dict):
                    for key in ("analysis", "synthesis", "plan"):
                        val = data.get(key)
                        if val and isinstance(val, str) and len(val) > 20:
                            await manager.send_json(session_id, {
                                "type": "result_chunk",
                                "key": key,
                                "content": val[:500],
                            })
                    report = data.get("report")
                    if report:
                        await manager.send_json(session_id, {
                            "type": "report_chunk",
                            "content": report,
                        })
                    pf = data.get("portfolio_allocation")
                    if pf:
                        await manager.send_json(session_id, {
                            "type": "portfolio",
                            "data": pf,
                        })
                    risk = data.get("risk_assessment")
                    if risk:
                        await manager.send_json(session_id, {
                            "type": "risk",
                            "data": risk,
                        })

            await asyncio.sleep(0.01)

        await manager.send_json(session_id, {
            "type": "complete",
            "message": "Research complete",
        })

    except WebSocketDisconnect:
        logger.info("Client %s disconnected", session_id)
    except Exception as e:
        logger.error("Stream error for %s: %s", session_id, e)
        try:
            await manager.send_json(session_id, {
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        manager.disconnect(session_id)
