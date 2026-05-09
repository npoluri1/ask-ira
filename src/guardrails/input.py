import re


class InputGuardrails:
    BLOCKED_PATTERNS = [
        r"(?i)\b(hack|exploit|vulnerability)\b",
        r"(?i)\b(insider.*(trade|info|tip))\b",
        r"(?i)\b(manipulat(e|ion)|pump.*dump)\b",
    ]

    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"\b\d{16}\b",
    ]

    async def check(self, query: str) -> dict:
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, query):
                return {
                    "blocked": True,
                    "reason": (
                        "Query contains prohibited terms "
                        "(insider trading/market manipulation)"
                    ),
                }

        for pattern in self.PII_PATTERNS:
            if re.search(pattern, query):
                return {
                    "blocked": True,
                    "reason": "Query appears to contain personally identifiable information",
                }

        if len(query) > 8000:
            return {"blocked": True, "reason": "Query exceeds maximum length of 8000 characters"}

        if len(query.strip()) < 3:
            return {"blocked": True, "reason": "Query too short"}

        return {"blocked": False, "reason": ""}
