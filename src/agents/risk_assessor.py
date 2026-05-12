"""Risk Assessment Agent.

Computes risk scores, VaR estimates, drawdown analysis,
and overall portfolio/investment risk ratings.
"""

from src.utils.llm import get_llm


class RiskAssessorAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.0)

    async def assess(self, query: str, context: dict) -> dict:
        research = context.get("mcp_results", {})
        analysis = context.get("analysis", "")
        tickers = context.get("servers", [])

        market_data = research.get("market_data", "")
        macro_data = research.get("macro", "")

        prompt = (
            f"Perform a comprehensive risk assessment.\n\n"
            f"Tickers: {', '.join(tickers) if tickers else 'N/A'}\n\n"
            f"Market Data:\n{market_data}\n\n"
            f"Macro Environment:\n{macro_data}\n\n"
            f"Prior Analysis:\n{analysis[:1500] if analysis else 'N/A'}\n\n"
            f"Return a structured assessment with:\n"
            f"1. Overall Risk Score (0.0-1.0, 1.0 = highest risk)\n"
            f"2. Key Risk Factors (market, sector, company-specific, macro)\n"
            f"3. VaR Estimate (95% confidence, 1-month horizon)\n"
            f"4. Maximum Drawdown Estimate\n"
            f"5. Risk/Reward Ratio\n"
            f"6. Mitigation Strategies"
        )

        result = await self.llm.ainvoke([
            ("system", "You are a chief risk officer at an investment firm. Be quantitative and precise."),  # noqa: E501
            ("human", prompt),
        ])

        return {
            "risk_assessment": result.content,
        }
