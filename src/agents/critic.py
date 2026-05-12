"""Critic/Reflection Agent.

Implements the reflection pattern — critiques the analyst's output
and writer's report, identifying gaps, biases, and errors.
Used as a quality gate before final output.
"""

from src.utils.llm import get_llm


class CriticAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.2)
        self.max_iterations = 2

    async def critique_analysis(self, query: str, analysis: str, context: dict) -> dict:
        prompt = (
            f"Critique this investment analysis. Identify:\n"
            f"1. Unsupported claims (no data backing)\n"
            f"2. Missing analysis dimensions\n"
            f"3. Cognitive biases (recency, confirmation, overconfidence)\n"
            f"4. Data quality issues\n"
            f"5. Contrarian viewpoints not considered\n\n"
            f"Query: {query}\n\n"
            f"Analysis:\n{analysis}\n\n"
            f"Rate the analysis quality (0.0-1.0) and list specific improvements."
        )

        result = await self.llm.ainvoke([
            ("system", "You are a rigorous investment review committee member. Be constructive but thorough."),  # noqa: E501
            ("human", prompt),
        ])

        return {"critique": result.content}

    async def critique_report(self, report: str) -> dict:
        prompt = (
            f"Review this investment research report. Check for:\n"
            f"1. Clarity and structure\n"
            f"2. Data-driven claims (are metrics cited?)\n"
            f"3. Balanced perspective (both bull and bear cases)\n"
            f"4. Actionable conclusions\n"
            f"5. Professional tone\n\n"
            f"Report:\n{report}\n\n"
            f"Score each dimension 0.0-1.0 and recommend: Approve / Revise / Reject."
        )

        result = await self.llm.ainvoke([
            ("system", "You are a senior editor reviewing a research report before publication."),
            ("human", prompt),
        ])

        return {"report_critique": result.content}
