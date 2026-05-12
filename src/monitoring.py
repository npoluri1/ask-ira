import logging
import time
from functools import wraps
from typing import Callable

from prometheus_client import Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger("ask-ira.metrics")

_request_timings: dict[str, list[float]] = {}
_request_counts: dict[str, int] = {}
_error_counts: dict[str, int] = {}

_prom_request_count = Counter(
    "ask_ira_requests_total", "Total requests", ["endpoint"]
)
_prom_error_count = Counter(
    "ask_ira_errors_total", "Total errors", ["endpoint"]
)
_prom_request_duration = Histogram(
    "ask_ira_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
_prom_active_requests = Gauge(
    "ask_ira_active_requests", "Active requests", ["endpoint"]
)
_prom_uptime = Gauge("ask_ira_uptime_seconds", "Service uptime in seconds")


def track_request(endpoint: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _prom_active_requests.labels(endpoint=endpoint).inc()
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                _request_counts[endpoint] = _request_counts.get(endpoint, 0) + 1
                _prom_request_count.labels(endpoint=endpoint).inc()
                return result
            except Exception:
                _error_counts[endpoint] = _error_counts.get(endpoint, 0) + 1
                _prom_error_count.labels(endpoint=endpoint).inc()
                raise
            finally:
                elapsed = time.perf_counter() - start
                _prom_request_duration.labels(endpoint=endpoint).observe(elapsed)
                _prom_active_requests.labels(endpoint=endpoint).dec()
                _request_timings.setdefault(endpoint, []).append(elapsed)
                if len(_request_timings[endpoint]) > 1000:
                    _request_timings[endpoint] = _request_timings[endpoint][-1000:]
        return wrapper
    return decorator


def get_metrics() -> dict:
    now = time.time()
    totals = {}
    for ep, timings in _request_timings.items():
        if timings:
            avg = sum(timings) / len(timings)
            p99 = sorted(timings)[int(len(timings) * 0.99)]
            totals[ep] = {
                "count": _request_counts.get(ep, 0),
                "errors": _error_counts.get(ep, 0),
                "avg_ms": round(avg * 1000, 2),
                "p99_ms": round(p99 * 1000, 2),
                "last_minute_rate": round(len([t for t in timings if t > now - 60]) / 60, 2),
            }
    return {
        "endpoints": totals,
        "total_requests": sum(_request_counts.values()),
        "total_errors": sum(_error_counts.values()),
        "uptime_seconds": round(now - _start_time),
    }


def get_prometheus_metrics() -> str:
    _prom_uptime.set(time.time() - _start_time)
    return generate_latest().decode("utf-8")


_start_time = time.time()


def get_health_status() -> dict:
    return {
        "status": "healthy",
        "version": "0.2.0",
        "service": "ask-ira",
        "uptime_seconds": round(time.time() - _start_time),
        "checks": {
            "api": "ok",
        },
    }
