from langchain_core.messages import HumanMessage, SystemMessage

from src.utils.llm import get_llm

SYSTEM_PROMPT = """You are the Writer Agent for Ask IRA.
Produce professional investment research reports.
Structure: Executive Summary | Company Overview | Financial Analysis |
Market Sentiment | Macro Context | Risks | Investment Thesis | Recommendation
Use clear formatting with markdown headings."""


class WriterAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.3, streaming=True)

    async def write(self, query: str, analysis_data: dict) -> dict:
        analysis = analysis_data.get("analysis", "")
        mcp_results = analysis_data.get("mcp_results", {})

        report = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Query: {query}\n\nAnalysis:\n{analysis}\n\n"
                    f"Research Data:\n"
                    f"{chr(10).join(f'{k}: {v}' for k, v in mcp_results.items())}\n\n"
                    "Write a comprehensive investment research report."
                )
            ),
        ])
        return {"report": report.content}
