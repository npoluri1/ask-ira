# API Development Standards

Rules for FastAPI endpoints, models, and middleware in `src/api/`.

## Endpoint Design

### REST Endpoints

```python
@router.post("/resource", response_model=ResponseModel)
async def create_resource(request: RequestModel):
    """Description of what this endpoint does."""
    result = await some_logic(request)
    return ResponseModel(...)
```

### WebSocket Endpoints

```python
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        await stream_research(data["query"], session_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(session_id)
```

## Request/Response Models

Use Pydantic v2 models in `src/api/models.py`:

```python
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    stream: bool = False
    risk_profile: str | None = None

class QueryResponse(BaseModel):
    report: str
    analysis: str | None = None
    mcp_results: dict[str, str] | None = None
    portfolio_allocation: dict | None = None
    risk_assessment: str | None = None
    confidence: float | None = None
    session_id: str = "default"
```

### Model Rules

1. Use `| None` for optional fields (Python 3.11+ syntax), not `Optional[...]`
2. Provide sensible defaults for all optional fields
3. Never expose secrets or internal state in responses
4. Add `response_model` to route decorators for OpenAPI schema generation

## Route Registration

```python
# src/api/routes.py
router = APIRouter(prefix="/api/v1")

# src/main.py
app.include_router(router)
```

## Streaming Responses

For streaming endpoints:
```python
@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    # Use async generator or return full response
    result = await graph.ainvoke(...)
    return QueryResponse(...)
```

## Error Handling

```python
# Global — in src/main.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred."},
    )
```

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable description"
}
```

## Graph Session Management

Graph instances are cached per `session_id`:

```python
_graphs: dict[str, any] = {}

def _get_graph(session_id: str):
    if session_id not in _graphs:
        _graphs[session_id] = create_graph(MCPRegistry())
    return _graphs[session_id]
```

## Middleware Stack Order

```python
app.add_middleware(CORSMiddleware, ...)        # 1st — CORS preflight
app.add_middleware(RequestLoggingMiddleware)    # 2nd — log all requests
app.add_middleware(RateLimitMiddleware, ...)     # 3rd — rate limit
app.add_middleware(SecurityHeadersMiddleware)    # 4th — add security headers
```

## Endpoint Listing

| Method | Path | Auth | Rate Limited | Description |
|--------|------|------|-------------|-------------|
| `GET` | `/` | No | No | Service info |
| `GET` | `/health` | No | No | Health check |
| `GET` | `/metrics` | No | No | Performance metrics |
| `GET` | `/ui` | No | No | Web dashboard |
| `GET` | `/docs` | No | No | Swagger UI |
| `GET` | `/redoc` | No | No | ReDoc |
| `POST` | `/api/v1/query` | No | Yes | Research query |
| `POST` | `/api/v1/query/stream` | No | Yes | Streaming query |
| `WS` | `/api/v1/ws/{id}` | No | Yes | WebSocket stream |
