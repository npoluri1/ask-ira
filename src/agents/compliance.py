"""Compliance Checker Agent.

Reviews research reports for regulatory compliance,
disclosure requirements, and prohibited content.
"""

import re

from src.utils.llm import get_llm

REGULATORY_KEYWORDS = [
    r"(?i)\b(guarantee|risk.free|no.risk|certain|sure.thing)\b",
    r"(?i)\b(insider|material.nonpublic)\b",
    r"(?i)\b(guaranteed.return|promised|assured)\b",
]

REQUIRED_DISCLAIMERS = [
    "past performance",
    "not financial advice",
    "consult your advisor",
]


class ComplianceAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.0)

    async def check(self, report: str) -> dict:
        issues = []

        for pattern in REGULATORY_KEYWORDS:
            matches = re.findall(pattern, report)
            if matches:
                issues.append({
                    "type": "regulatory_keyword",
                    "severity": "high",
                    "detail": f"Potentially problematic language: {', '.join(set(matches))}",
                })

        report_lower = report.lower()
        for disclaimer in REQUIRED_DISCLAIMERS:
            if disclaimer not in report_lower:
                issues.append({
                    "type": "missing_disclaimer",
                    "severity": "medium",
                    "detail": f"Missing required disclaimer: '{disclaimer}'",
                })

        result = await self.llm.ainvoke([
            ("system", "You are a financial compliance officer. Identify any regulatory issues in this research report."),
            ("human", f"Review this report for compliance issues:\n\n{report[:3000]}"),
        ])

        return {
            "compliance_issues": issues,
            "compliance_review": result.content,
            "compliant": len([i for i in issues if i["severity"] == "high"]) == 0,
        }
