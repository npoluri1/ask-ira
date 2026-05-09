import re


class OutputGuardrails:
    HALLUCINATION_MARKERS = [
        r"(?i)\bI am not sure\b",
        r"(?i)\bI don't have (that )?(data|information)\b",
        r"(?i)\bI cannot provide (an answer|a recommendation|specific advice)\b",
    ]

    SENSITIVE_PATTERNS = [
        r"(?i)\b(confidential|proprietary|trade.?secret)\b",
    ]

    async def check(self, report: str) -> dict:
        if not report:
            return {"blocked": True, "reason": "Empty report generated"}

        if len(report) < 50:
            return {"blocked": True, "reason": "Report too short to be meaningful"}

        for pattern in self.HALLUCINATION_MARKERS:
            if re.search(pattern, report):
                return {
                    "blocked": True,
                    "reason": "Report contains hallucination markers (uncertainty language)",
                }

        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, report):
                return {
                    "blocked": True,
                    "reason": "Report may contain confidential/proprietary content",
                }

        return {"blocked": False, "reason": ""}
