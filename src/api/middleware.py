import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ask-ira")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        elapsed = time.time() - start
        logger.info(
            "%s %s -> %d (%.2fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
        return response
