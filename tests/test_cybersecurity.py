import pytest
from src.cybersecurity import (
    WebApplicationFirewall,
    IntrusionDetectionSystem,
    SIEMEngine,
    DDoSProtection,
    InputSanitizer,
    VulnerabilityScanner,
    IDS_ALERTS,
    run_security_check,
)


@pytest.fixture
def waf():
    return WebApplicationFirewall()


@pytest.fixture
def ids():
    return IntrusionDetectionSystem()


@pytest.fixture
def siem():
    return SIEMEngine()


@pytest.mark.asyncio
async def test_waf_blocks_sql_injection(waf):
    result = waf.check_request("POST", "/query", {}, "SELECT * FROM users; UNION ALL SELECT * FROM passwords;'", "1.2.3.4")
    assert result["blocked"] is True
    assert any("sql_injection" in flag for flag in result["flags"])


@pytest.mark.asyncio
async def test_waf_blocks_xss(waf):
    result = waf.check_request("POST", "/query", {}, "<script>alert('xss')</script>", "1.2.3.4")
    assert result["blocked"] is True
    assert any("xss" in flag for flag in result["flags"])


@pytest.mark.asyncio
async def test_waf_blocks_path_traversal(waf):
    result = waf.check_request("GET", "../../../etc/passwd", {}, "", "1.2.3.4")
    assert result["blocked"] is True
    assert any("path_traversal" in flag for flag in result["flags"])


@pytest.mark.asyncio
async def test_waf_passes_clean_request(waf):
    result = waf.check_request("GET", "/api/v1/market/indices", {}, "", "1.2.3.4")
    assert result["blocked"] is False


@pytest.mark.asyncio
async def test_waf_blocks_command_injection(waf):
    result = waf.check_request("POST", "/query", {}, "; ls -la && echo `whoami`", "1.2.3.4")
    assert result["blocked"] is True


@pytest.mark.asyncio
async def test_ids_detect_port_scan(ids):
    for _ in range(60):
        ids.detect("port_scan", "192.168.1.1", {"port": 80})
    alerts = ids.get_alerts(severity="medium")
    assert len(alerts) > 0


@pytest.mark.asyncio
async def test_ids_detect_brute_force(ids):
    for _ in range(25):
        ids.detect("auth_attempt", "10.0.0.1", {"path": "/api/v1/auth/login"})
    alerts = ids.get_alerts(severity="critical")
    assert len(alerts) > 0


@pytest.mark.asyncio
async def test_ids_get_alerts_empty():
    IDS_ALERTS.clear()
    ids = IntrusionDetectionSystem()
    alerts = ids.get_alerts()
    assert alerts == []


@pytest.mark.asyncio
async def test_siem_ingest_log(siem):
    siem.ingest_log("test_source", "test_event", {"key": "value"}, "low")
    logs = siem.search_logs("test_event")
    assert len(logs) > 0
    assert logs[0]["event_type"] == "test_event"


@pytest.mark.asyncio
async def test_siem_alert_correlation(siem):
    for _ in range(5):
        siem.ingest_log("auth", "failed_login", {"ip": "1.2.3.4"}, "medium")
    siem.ingest_log("auth", "login_success", {"ip": "1.2.3.4"}, "info")
    incidents = siem.correlate()
    assert isinstance(incidents, list)


@pytest.mark.asyncio
async def test_ddos_detect_attack():
    ddos = DDoSProtection()
    for _ in range(505):
        ddos.check_request("5.6.7.8", 100)
    result = ddos.check_request("5.6.7.8", 100)
    assert result["blocked"] is True


@pytest.mark.asyncio
async def test_ddos_normal_traffic():
    ddos = DDoSProtection()
    for _ in range(5):
        ddos.check_request("9.10.11.12", 100)
    result = ddos.check_request("9.10.11.12", 100)
    assert result["blocked"] is False


@pytest.mark.asyncio
async def test_run_security_check_blocks_attack():
    result = run_security_check({
        "ip": "1.2.3.4",
        "method": "POST",
        "path": "/api/v1/query",
        "body": "<script>alert('x')</script>",
        "headers": {},
        "bytes": 50,
        "query": "",
    })
    assert result["blocked"] is True


@pytest.mark.asyncio
async def test_run_security_check_passes_clean():
    result = run_security_check({
        "ip": "1.2.3.4",
        "method": "GET",
        "path": "/health",
        "body": "",
        "headers": {},
        "bytes": 0,
        "query": "",
    })
    assert result["blocked"] is False


@pytest.mark.asyncio
async def test_input_sanitizer_removes_xss():
    cleaned = InputSanitizer.sanitize_string("<script>alert('x')</script>Hello")
    assert "<script>" not in cleaned
    assert "Hello" in cleaned


@pytest.mark.asyncio
async def test_vulnerability_scanner():
    scanner = VulnerabilityScanner()
    result = scanner.run_scan("full")
    assert isinstance(result["findings"], list)
