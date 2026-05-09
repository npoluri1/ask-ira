import pytest

from src.monitoring import get_health_status, get_metrics


def test_get_health_status():
    status = get_health_status()
    assert status["status"] == "healthy"
    assert status["service"] == "ask-ira"
    assert status["version"] == "0.2.0"
    assert "uptime_seconds" in status
    assert "checks" in status


def test_get_metrics():
    metrics = get_metrics()
    assert "endpoints" in metrics
    assert "total_requests" in metrics
    assert "total_errors" in metrics
    assert "uptime_seconds" in metrics
