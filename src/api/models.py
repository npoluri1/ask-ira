from typing import Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    stream: bool = False
    risk_profile: str | None = None


class QueryResponse(BaseModel):
    report: str
    analysis: str | None = None
    mcp_results: dict[str, Any] | None = None
    portfolio_allocation: dict | None = None
    risk_assessment: str | None = None
    confidence: float | None = None
    session_id: str = "default"
