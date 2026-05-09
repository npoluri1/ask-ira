import json
import re

from src.mcp_servers.registry import MCPRegistry
from src.utils.llm import get_llm


class SupervisorAgent:
    def __init__(self, registry: MCPRegistry):
        self.registry = registry
        self.llm = get_llm(temperature=0.0)
        self._server_names = registry.server_names

    async def plan(self, query: str) -> dict:
        server_list = ", ".join(self._server_names)
        prompt = (
            f"You are a routing supervisor for an investment research system.\n\n"
            f"Query: {query}\n\n"
            f"Available MCP servers: {server_list}\n\n"
            f"Decide:\n"
            f"1. Which servers to query (comma-separated, subset of available)\n"
            f"2. Whether RAG retrieval is needed (true/false)\n"
            f"3. Risk profile: conservative / moderate / aggressive\n"
            f"4. Research dimensions to analyze (comma-separated)\n"
            f"5. Next agent: 'researcher' to proceed\n\n"
            f"Output JSON only:\n"
            f"{'{'} \"servers\": [...], \"use_rag\": bool, \"risk_profile\": \"...\", "
            f"\"dimensions\": [...], \"next\": \"researcher\", "
            f"\"plan\": \"brief research plan\" {'}'}"
        )

        result = await self.llm.ainvoke([
            ("system", "You are a precise routing supervisor. Output only valid JSON."),
            ("human", prompt),
        ])

        return self._parse_plan(result.content)

    def _parse_plan(self, raw: str) -> dict:
        try:
            json_str = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_str:
                plan = json.loads(json_str.group())
                servers = plan.get("servers", [])
                valid = [s for s in servers if s in self._server_names]
                return {
                    "plan": plan.get("plan", raw[:200]),
                    "servers": valid or self._server_names[:2],
                    "use_rag": plan.get("use_rag", True),
                    "dimensions": plan.get("dimensions", []),
                    "risk_profile": plan.get("risk_profile", "moderate"),
                    "next": "researcher",
                }
        except (json.JSONDecodeError, AttributeError):
            pass

        return {
            "plan": raw[:200],
            "servers": self._server_names[:2],
            "use_rag": True,
            "dimensions": ["financials", "sentiment", "macro"],
            "risk_profile": "moderate",
            "next": "researcher",
        }
