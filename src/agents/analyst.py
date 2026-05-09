import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.utils.llm import get_llm

SYSTEM_PROMPT = """You are the Analyst Agent for Ask IRA.
Analyze research data and produce investment insights.
Assess: financial health, market sentiment, macro environment, risks, opportunities.
Rate confidence as 0.0-1.0 based on data quality and alignment.

End your analysis with a line exactly like:
CONFIDENCE: 0.85"""


class AnalystAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.2)

    async def analyze(self, query: str, research_data: dict) -> dict:
        mcp_results = research_data.get("mcp_results", {})
        synthesis = research_data.get("synthesis", "")
        rag_context = research_data.get("rag_context", [])

        context_parts = [f"Research synthesis: {synthesis}"]
        for name, content in mcp_results.items():
            context_parts.append(f"[{name}]: {content}")
        if rag_context:
            context_parts.append(f"Internal knowledge:\n{chr(10).join(rag_context)}")

        analysis = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Query: {query}\n\n{chr(10).join(context_parts)}\n\n"
                        "Provide investment analysis with confidence score."
            ),
        ])

        text = analysis.content
        confidence = None
        match = re.search(r"CONFIDENCE:\s*([01]\.\d+)", text)
        if match:
            confidence = float(match.group(1))
        return {
            "analysis": text,
            "confidence": confidence,
        }
