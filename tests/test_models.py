import pytest
from pydantic import ValidationError

from src.api.models import QueryRequest, QueryResponse


def test_query_request_defaults():
    req = QueryRequest(query="Analyze AAPL")
    assert req.query == "Analyze AAPL"
    assert req.session_id == "default"
    assert req.stream is False
    assert req.risk_profile is None


def test_query_request_with_all_fields():
    req = QueryRequest(
        query="MSFT outlook",
        session_id="test-123",
        stream=True,
        risk_profile="aggressive",
    )
    assert req.query == "MSFT outlook"
    assert req.session_id == "test-123"
    assert req.stream is True
    assert req.risk_profile == "aggressive"


def test_query_request_missing_query():
    with pytest.raises(ValidationError):
        QueryRequest()


def test_query_response_defaults():
    resp = QueryResponse(report="Test report")
    assert resp.report == "Test report"
    assert resp.session_id == "default"
    assert resp.analysis is None
    assert resp.confidence is None
    assert resp.portfolio_allocation is None


def test_query_response_with_all_fields():
    resp = QueryResponse(
        report="Full report",
        analysis="Good analysis",
        mcp_results={"market_data": "data"},
        portfolio_allocation={"equities": 0.6},
        risk_assessment="Low risk",
        confidence=0.85,
        session_id="sess-1",
    )
    assert resp.confidence == 0.85
    assert resp.portfolio_allocation["equities"] == 0.6
    assert resp.risk_assessment == "Low risk"
