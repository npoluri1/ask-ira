# Guardrails & Security Standards

Security rules for `src/guardrails/`, `src/middleware.py`, `src/agents/compliance.py`.

## Security Layer Architecture

```
Layer 1: Transport    → HTTPS, HSTS, CORS
Layer 2: Request      → Rate limiting, request ID, size limits
Layer 3: Input Guard  → Blocked patterns, PII, length validation
Layer 4: Agentic      → Compliance agent, reflection loop, HITL
Layer 5: Output Guard → Hallucination, sensitive content, length
Layer 6: Response     → Security headers, no stack traces
```

## Input Guardrails (`src/guardrails/input.py`)

### Blocked Patterns (always block)

| Category | Pattern | Severity |
|----------|---------|----------|
| Hacking | `hack`, `exploit`, `vulnerability` | Critical |
| Insider trading | `insider.*trade`, `insider.*info`, `insider.*tip` | Critical |
| Market manipulation | `manipulation`, `pump.*dump` | Critical |

### PII Detection (always block)

| Pattern | Example |
|---------|---------|
| SSN | `123-45-6789` (regex: `\d{3}-\d{2}-\d{4}`) |
| Credit card | 16 consecutive digits (regex: `\d{16}`) |

### Length Rules

- Minimum: 3 characters (block queries like "hi", "a")
- Maximum: 8000 characters (block excessively long queries)

### Guardrail Implementation Pattern

```python
async def check(self, query: str) -> dict:
    for pattern in self.BLOCKED_PATTERNS:
        if re.search(pattern, query):
            return {"blocked": True, "reason": "..."}
    # ... PII checks, length checks ...
    return {"blocked": False, "reason": ""}
```

## Output Guardrails (`src/guardrails/output.py`)

### Hallucination Markers (flag as blocked)

| Pattern | Example |
|---------|---------|
| `I am not sure` | Indicates low confidence |
| `I don't have data/information` | Lack of grounding |
| `I cannot provide` | Refusal to answer |

### Sensitive Content (flag as blocked)

| Pattern | Example |
|---------|---------|
| `confidential` | May leak proprietary data |
| `proprietary` | Protected information |
| `trade.?secret` | Trade secrets |

### Length Rule

- Minimum: 50 characters (block empty/truncated reports)

## Compliance Agent (`src/agents/compliance.py`)

### Regulatory Keywords (flag as high severity)

- `guarantee`, `risk.?free`, `no.?risk`, `certain`, `sure.?thing`
- `insider`, `material.?nonpublic`
- `guaranteed.?return`, `promised`, `assured`

### Required Disclaimers (flag as medium severity)

- Must contain: "past performance"
- Must contain: "not financial advice"
- Must contain: "consult your advisor"

### Compliance Implementation

```python
class ComplianceAgent:
    async def check(self, report: str) -> dict:
        issues = []
        for pattern in REGULATORY_KEYWORDS:
            if re.search(pattern, report):
                issues.append({"type": "regulatory_keyword", "severity": "high", ...})
        for disclaimer in REQUIRED_DISCLAIMERS:
            if disclaimer not in report.lower():
                issues.append({"type": "missing_disclaimer", "severity": "medium", ...})
        return {"compliance_issues": issues, "compliant": len(high_severity) == 0}
```

## Middleware Security (`src/middleware.py`)

| Middleware | Rule |
|------------|------|
| `RateLimitMiddleware` | 100 requests/minute per IP (configurable) |
| `SecurityHeadersMiddleware` | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security`, `Cache-Control: no-store` |
| `RequestIDMiddleware` | Add `X-Request-ID` header to every response |

## API Security (`src/main.py`)

- CORS: configurable from `CORS_ORIGINS` env var (default `*`)
- Global exception handler: returns `{"error": "internal_server_error"}` — never exposes stack traces
- Config validation (`validate_config()`): fails startup if API keys missing in production

## Prohibited Actions

1. Never log API keys, tokens, or secrets
2. Never expose internal tracebacks or debug info in production
3. Never accept raw file paths or shell commands from user input
4. Never allow modification of system prompts via user input
5. Never skip guardrails for any user role

## Adding New Security Rules

1. Add regex pattern to the appropriate guardrails class
2. Add corresponding test in `tests/test_agents.py`
3. Update severity classification (high/medium/low)
4. Document the rule in the appropriate `.claude/*.md` file
