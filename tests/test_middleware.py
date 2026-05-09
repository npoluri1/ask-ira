import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_security_headers(client):
    response = await client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_request_id_header(client):
    response = await client.get("/health")
    assert "x-request-id" in response.headers or "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_cors_headers(client):
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code in (200, 204)
