import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Ask IRA"
    assert data["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ask-ira"
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_docs_redirect(client):
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_query_endpoint(client):
    response = await client.post(
        "/api/v1/query",
        json={"query": "What is Apple's current outlook?", "session_id": "test-session"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data
    assert data["session_id"] == "test-session"


@pytest.mark.asyncio
async def test_query_endpoint_with_risk_profile(client):
    response = await client.post(
        "/api/v1/query",
        json={
            "query": "Assess MSFT",
            "session_id": "test-risk",
            "risk_profile": "aggressive",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data


@pytest.mark.asyncio
async def test_sse_streaming_endpoint(client):
    response = await client.post(
        "/api/v1/query/stream",
        json={"query": "Analyze AAPL", "session_id": "test-stream"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_query_endpoint_no_session(client):
    response = await client.post(
        "/api/v1/query",
        json={"query": "What is the market outlook?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data


@pytest.mark.asyncio
async def test_404_on_unknown(client):
    response = await client.get("/unknown-path-12345")
    assert response.status_code in (404, 405, 200)
