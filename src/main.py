from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.middleware import RequestLoggingMiddleware
from src.api.routes import router
from src.cache import get_cache
from src.config import get_settings, validate_config
from src.config.logging import setup_logging
from src.middleware import RateLimitMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware
from src.monitoring import get_health_status, get_metrics

logger = setup_logging()
settings = get_settings()
validate_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ask IRA starting up...")
    logger.info("Embedding model: %s", settings.embedding_model)
    logger.info("LangSmith tracing: %s", settings.langsmith_tracing)
    logger.info("Environment: %s", settings.environment)

    if settings.cache_enabled:
        cache = get_cache()
        await cache.clear()
        logger.info("Response cache initialized")

    app.state.cache = get_cache()

    yield

    logger.info("Ask IRA shutting down...")
    cache = get_cache()
    await cache.clear()


app = FastAPI(
    title="Ask IRA - Investment Research Agent",
    description=(
        "Production-grade investment research agent powered by "
        "LangGraph multi-agent orchestration, MCP dynamic tool discovery, "
        "and hybrid RAG pipeline. Supports streaming, HITL review, "
        "portfolio management, risk assessment, and compliance checking."
    ),
    version="0.2.0",
    lifespan=lifespan,
    contact={"name": "IRA Team", "url": "https://github.com/your-org/ask-ira"},
    license_info={"name": "MIT"},
)

cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_max,
    window_seconds=settings.rate_limit_window,
)
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health", tags=["System"])
async def health():
    return get_health_status()


@app.get("/metrics", tags=["System"])
async def metrics():
    return get_metrics()


@app.get("/", tags=["System"])
async def root():
    return RedirectResponse(url="/ui/")


app.include_router(router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred."},
    )


def main():
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        workers=2,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
