"""Portfolio Manager Agent.

Allocates portfolios, suggests rebalancing, and optimizes
asset allocation based on risk tolerance and market conditions.
"""

from src.utils.llm import get_llm

ALLOCATION_MODELS = {
    "conservative": {"equities": 0.30, "bonds": 0.50, "cash": 0.15, "alternatives": 0.05},
    "moderate": {"equities": 0.55, "bonds": 0.30, "cash": 0.10, "alternatives": 0.05},
    "aggressive": {"equities": 0.80, "bonds": 0.10, "cash": 0.05, "alternatives": 0.05},
}


class PortfolioManagerAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.1)

    async def build_portfolio(self, query: str, context: dict) -> dict:
        risk_profile = context.get("risk_profile", "moderate")
        model = ALLOCATION_MODELS.get(risk_profile, ALLOCATION_MODELS["moderate"])

        tickers = context.get("servers", [])[:5]
        research = context.get("mcp_results", {})
        analysis = context.get("analysis", "")

        prompt = (
            f"Given the following research and analysis, build a diversified portfolio.\n\n"
            f"Risk Profile: {risk_profile}\n"
            f"Target Allocation: {model}\n"
            f"Available Securities: {', '.join(tickers) if tickers else 'Broad market'}\n\n"
            f"Research Data:\n{str(research)[:1000]}\n\n"
            f"Analysis:\n{analysis[:1000] if analysis else 'N/A'}\n\n"
            f"Output a portfolio allocation with:\n"
            f"1. Positions with weights (must sum to 1.0)\n"
            f"2. Expected return and risk estimates\n"
            f"3. Rebalancing recommendations\n"
            f"4. Diversification score (0.0-1.0)"
        )

        result = await self.llm.ainvoke([
            ("system", "You are a professional portfolio manager. Output structured portfolio allocations."),  # noqa: E501
            ("human", prompt),
        ])

        return {
            "allocation": model,
            "recommendation": result.content,
            "risk_profile": risk_profile,
        }
