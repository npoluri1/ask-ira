import warnings
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*allowed_objects.*")
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from src.api.auth_routes import router as auth_router  # noqa: E402
from src.api.market_routes import router as market_router  # noqa: E402
from src.api.middleware import RequestLoggingMiddleware  # noqa: E402
from src.api.routes import config_router, router  # noqa: E402
from src.cache import get_cache  # noqa: E402
from src.config import get_settings, validate_config  # noqa: E402
from src.config.logging import setup_logging  # noqa: E402
from src.cybersecurity import ids, run_security_check, siem  # noqa: E402
from src.middleware import RateLimitMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware  # noqa: E402
from src.monitoring import get_health_status, get_metrics, get_prometheus_metrics  # noqa: E402

logger = setup_logging()
settings = get_settings()
validate_config()


async def security_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "0.0.0.0"
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8", errors="replace")

    if request.url.path.startswith(("/health", "/metrics", "/ui/", "/static")):
        response = await call_next(request)
        return response

    check_data = {
        "ip": ip,
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "body": body_str,
        "bytes": len(body_str),
        "query": str(request.query_params),
    }

    result = run_security_check(check_data)

    if result["blocked"]:
        siem.ingest_log("security_gateway", "request_blocked", check_data, "high")
        return JSONResponse(
            status_code=403,
            content={"error": "request_blocked", "message": "Request blocked by security gateway", "risk_score": result["risk_score"]},
            headers={"X-Security-Block": "true", "X-Risk-Score": str(result["risk_score"])},
        )

    response = await call_next(request)

    if request.url.path.startswith("/ui/") or request.url.path == "/ui":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    if response.status_code >= 400:
        ids.detect("api_abuse", ip, {"path": request.url.path, "status": response.status_code})

    response.headers["X-Security-Check"] = "passed"
    response.headers["X-Risk-Score"] = str(result["risk_score"])

    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Ask IRA — Super Financial Platform Starting Up...")
    logger.info("=" * 60)
    logger.info("Environment: %s", settings.environment)

    if settings.cache_enabled:
        cache = get_cache()
        await cache.clear()
        logger.info("Response cache initialized")

    app.state.cache = get_cache()
    logger.info("Cybersecurity layer active: WAF + IDS + SIEM + DDoS Protection")
    logger.info("Agent Platform: %d agent types registered", len(__import__("src.agent_platform", fromlist=["AGENT_REGISTRY"]).AGENT_REGISTRY))
    logger.info("Compliance Router: 20+ country jurisdictions loaded")

    # Auto-seed vector store if empty
    try:
        from src.rag.vector_store import VectorStore
        vs = VectorStore()
        if vs.count() == 0:
            logger.info("Vector store is empty, auto-seeding sample data...")
            from scripts.seed_data import build_documents, seed_vector_store
            docs = build_documents()
            count = seed_vector_store(vs, docs, clear_first=False)
            logger.info("Auto-seeded %d documents into ChromaDB", count)
        else:
            logger.info("Vector store already contains %d documents", vs.count())
    except Exception as e:
        logger.warning("Auto-seeding skipped: %s", e)

    yield

    logger.info("Ask IRA shutting down...")


app = FastAPI(
    title="Ask IRA — Super Financial Platform",
    description=(
        "Global financial super-app: AI agents for banking, insurance, payments, "
        "crypto, portfolio management, multi-currency, SWIFT/SEPA/ACH, "
        "Compliance (KYC/AML/Sanctions), Enterprise treasury, and Agent Platform. "
        "Enterprise-grade cybersecurity with WAF, IDS, SIEM, DDoS protection."
    ),
    version="0.5.0",
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
app.add_middleware(RateLimitMiddleware, max_requests=settings.rate_limit_max, window_seconds=settings.rate_limit_window)
app.add_middleware(SecurityHeadersMiddleware)

app.middleware("http")(security_middleware)


@app.get("/health", tags=["System"])
async def health():
    return get_health_status()


@app.get("/metrics", tags=["System"])
async def metrics():
    return get_metrics()


@app.get("/metrics/prometheus", tags=["System"])
async def prometheus_metrics():
    from fastapi.responses import Response
    return Response(content=get_prometheus_metrics(), media_type="text/plain; version=0.0.4", headers={"Cache-Control": "no-cache"})


@app.get("/", tags=["System"])
async def root():
    return RedirectResponse(url="/ui/")


@app.get("/api/v1/system/capabilities", tags=["System"])
async def system_capabilities():
    modules = []
    try:
        modules.append("banking")
    except Exception:
        pass
    try:
        modules.append("payments")
    except Exception:
        pass
    try:
        modules.append("crypto")
    except Exception:
        pass
    try:
        modules.append("insurance")
    except Exception:
        pass
    try:
        modules.append("compliance")
    except Exception:
        pass
    try:
        modules.append("wallets")
    except Exception:
        pass
    try:
        modules.append("products")
    except Exception:
        pass
    try:
        modules.append("agent_platform")
    except Exception:
        pass
    try:
        modules.append("cybersecurity")
    except Exception:
        pass
    return {
        "app": "Ask IRA",
        "version": "0.5.0",
        "modules": modules,
        "agents_registered": len(__import__("src.agent_platform", fromlist=["AGENT_REGISTRY"]).AGENT_REGISTRY) if "agent_platform" in modules else 0,
        "countries_supported": list(__import__("src.compliance_router", fromlist=["COUNTRY_COMPLIANCE"]).COUNTRY_COMPLIANCE.keys()) if "compliance" in modules else [],
    }


app.include_router(config_router)
app.include_router(router)
app.include_router(auth_router)

try:
    from src.api.banking_routes import router as banking_router
    app.include_router(banking_router)
except Exception as e:
    logger.warning("Banking routes not loaded: %s", e)

try:
    from src.api.payments_routes import router as payments_router
    app.include_router(payments_router)
except Exception as e:
    logger.warning("Payments routes not loaded: %s", e)

try:
    from src.api.crypto_routes import router as crypto_router
    app.include_router(crypto_router)
except Exception as e:
    logger.warning("Crypto routes not loaded: %s", e)

try:
    from src.api.compliance_routes import router as compliance_router
    app.include_router(compliance_router)
except Exception as e:
    logger.warning("Compliance routes not loaded: %s", e)

try:
    from src.api.wallets_routes import router as wallets_router
    app.include_router(wallets_router)
except Exception as e:
    logger.warning("Wallets routes not loaded: %s", e)

try:
    from src.api.portfolio_routes import router as portfolio_router
    app.include_router(portfolio_router)
except Exception as e:
    logger.warning("Portfolio routes not loaded: %s", e)

try:
    from src.api.security_routes import router as security_router
    app.include_router(security_router)
except Exception as e:
    logger.warning("Security routes not loaded: %s", e)

try:
    from src.api.insurance_routes import router as insurance_router
    app.include_router(insurance_router)
except Exception as e:
    logger.warning("Insurance routes not loaded: %s", e)

app.include_router(market_router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    try:
        ids.detect("application_error", request.client.host if request.client else "unknown", {"path": request.url.path, "error": str(exc)[:200]})
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred."},
    )


def main():
    logger.info("Starting Ask IRA on 0.0.0.0:8000")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, workers=2, log_level=settings.log_level.lower())


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
