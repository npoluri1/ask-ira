from fastapi import APIRouter, Request

from src.cybersecurity import (
    ddos,
    get_security_headers,
    ids,
    incident_response,
    run_security_check,
    scanner,
    siem,
    threat_intel,
    waf,
)

router = APIRouter(prefix="/api/v1/security")


@router.post("/check")
async def security_check(request: Request):
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    data = {
        "ip": request.client.host if request.client else "0.0.0.0",
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "body": str(body),
        "bytes": len(str(body)),
        "query": str(request.query_params),
    }
    return run_security_check(data)


@router.get("/waf/stats")
async def waf_stats():
    return waf.get_stats()


@router.post("/waf/block-ip")
async def block_ip(ip: str):
    waf.block_ip(ip)
    return {"status": "blocked", "ip": ip}


@router.post("/waf/unblock-ip")
async def unblock_ip(ip: str):
    waf.unblock_ip(ip)
    return {"status": "unblocked", "ip": ip}


@router.get("/ids/events")
async def ids_events(source_ip: str | None = None, event_type: str | None = None, limit: int = 100):
    return {"events": ids.get_events(source_ip, event_type, limit)}


@router.get("/ids/alerts")
async def ids_alerts(severity: str | None = None, limit: int = 50):
    return {"alerts": ids.get_alerts(severity, limit)}


@router.get("/ids/rules")
async def ids_rules():
    return {"rules": ids.get_rules()}


@router.get("/ids/stats")
async def ids_stats():
    return ids.get_stats()


@router.get("/siem/logs")
async def siem_logs(query: str = "", limit: int = 50):
    if query:
        return {"logs": siem.search_logs(query, limit)}
    return {"logs": siem.search_logs("", limit)}


@router.get("/siem/correlate")
async def siem_correlate():
    return {"incidents": siem.correlate()}


@router.get("/siem/stats")
async def siem_stats():
    return siem.get_stats()


@router.get("/ddos/stats")
async def ddos_stats():
    return ddos.get_stats()


@router.post("/ddos/whitelist")
async def ddos_whitelist(ip: str):
    ddos.whitelist_ip(ip)
    return {"status": "whitelisted", "ip": ip}


@router.post("/ddos/unblock")
async def ddos_unblock(ip: str):
    ddos.unblock_ip(ip)
    return {"status": "unblocked", "ip": ip}


@router.post("/vulnerability/scan")
async def run_scan(scan_type: str = "full"):
    return scanner.run_scan(scan_type)


@router.get("/vulnerability/scans")
async def scan_history(limit: int = 10):
    return {"scans": scanner.get_scan_history(limit)}


@router.get("/incidents")
async def list_incidents(severity: str | None = None, status: str | None = None, limit: int = 50):
    return {"incidents": incident_response.get_incidents(severity, status, limit)}


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, resolution: str = "Resolved via automated response"):
    return incident_response.resolve_incident(incident_id, resolution)


@router.get("/incidents/stats")
async def incident_stats():
    return incident_response.get_stats()


@router.get("/threat-intel/check-ip")
async def check_ip(ip: str):
    return threat_intel.check_ip(ip)


@router.get("/threat-intel/check-domain")
async def check_domain(domain: str):
    return threat_intel.check_domain(domain)


@router.get("/threat-intel/stats")
async def threat_intel_stats():
    return threat_intel.get_stats()


@router.get("/headers")
async def security_headers():
    return get_security_headers()


@router.get("/overview")
async def security_overview():
    return {
        "waf": waf.get_stats(),
        "ids": ids.get_stats(),
        "siem": siem.get_stats(),
        "ddos": ddos.get_stats(),
        "incidents": incident_response.get_stats(),
        "threat_intel": threat_intel.get_stats(),
        "last_scan": scanner.get_last_scan(),
    }
