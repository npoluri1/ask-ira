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


manager = ConnectionManager()


async def stream_research(query: str, session_id: str, websocket: WebSocket):
    await manager.connect(session_id, websocket)

    try:
        await manager.send_json(session_id, {"type": "status", "stage": "starting", "message": "Initializing research..."})

        graph = create_graph(MCPRegistry())
        config = {"configurable": {"thread_id": session_id}}

        await manager.send_json(session_id, {"type": "status", "stage": "guard_input", "message": "Checking input safety..."})

        stages = {
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

            if kind == "on_chain_start" and name in stages:
                await manager.send_json(session_id, {
                    "type": "status",
                    "stage": name,
                    "message": stages[name],
                })

            if kind == "on_chain_end" and name == "writer":
                data = event.get("data", {}).get("output", {})
                if isinstance(data, dict) and "report" in data:
                    await manager.send_json(session_id, {
                        "type": "report_chunk",
                        "content": data["report"],
                    })

            await asyncio.sleep(0.01)

        await manager.send_json(session_id, {"type": "complete", "message": "Research complete"})

    except WebSocketDisconnect:
        logger.info("Client %s disconnected", session_id)
    except Exception as e:
        logger.error("Stream error for %s: %s", session_id, e)
        await manager.send_json(session_id, {"type": "error", "message": str(e)})
    finally:
        manager.disconnect(session_id)
