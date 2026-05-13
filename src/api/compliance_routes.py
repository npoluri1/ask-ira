from fastapi import APIRouter, Query

from src.compliance import aml, kyc, reporting, sanctions
from src.compliance_router import compliance_router

router = APIRouter(prefix="/api/v1/compliance")

_aml_engine = aml
_sanctions_engine = sanctions
_kyc_engine = kyc
_reporting_engine = reporting

# Seed demo compliance data
_kyc_engine.create_demo_data("demo")
_aml_engine.create_demo_data("demo")
_sanctions_engine.create_demo_data()


@router.get("/countries")
async def compliance_countries():
    return {"countries": compliance_router.get_all_countries()}


def _get_user_id() -> str:
    return "demo"


@router.post("/aml/screen-user")
async def screen_user(body: dict):
    return _aml_engine.screen_user(
        user_id=_get_user_id(),
        name=body["name"],
        date_of_birth=body.get("date_of_birth", ""),
        nationality=body.get("nationality", ""),
        country_of_residence=body.get("country_of_residence", ""),
    )


@router.post("/aml/screen-transaction")
async def screen_transaction(body: dict):
    return _aml_engine.screen_transaction(
        user_id=_get_user_id(),
        amount=body["amount"],
        currency=body.get("currency", "USD"),
        counterparty=body.get("counterparty", ""),
        country=body.get("country", ""),
    )


@router.get("/aml/high-risk-countries")
async def high_risk_countries():
    return {"countries": _aml_engine.get_high_risk_countries()}


@router.get("/aml/history")
async def aml_history():
    return {"history": _aml_engine.get_screening_history(_get_user_id())}


@router.post("/aml/file-sar")
async def file_sar(body: dict):
    return _aml_engine.file_sar(
        user_id=_get_user_id(),
        transaction_id=body["transaction_id"],
        reason=body["reason"],
        details=body.get("details", ""),
    )


@router.post("/aml/check-structuring")
async def check_structuring(body: dict):
    return {"alerts": _aml_engine.check_structuring(body.get("transactions", []))}


@router.post("/sanctions/check-name")
async def check_name(body: dict):
    return {"matches": _sanctions_engine.check_name(body["name"])}


@router.post("/sanctions/check-entity")
async def check_entity(body: dict):
    return {"matches": _sanctions_engine.check_entity(
        entity_name=body["entity_name"],
        country=body.get("country", ""),
    )}


@router.post("/sanctions/check-country")
async def check_country(body: dict):
    return _sanctions_engine.check_country(body["country"])


@router.get("/sanctions/restricted-countries")
async def restricted_countries():
    return {"restricted_countries": _sanctions_engine.get_restricted_countries()}


@router.get("/sanctions/summary")
async def sanctions_summary():
    return {"summary": _sanctions_engine.get_sanctions_summary()}


@router.post("/kyc/start")
async def start_kyc(body: dict):
    return _kyc_engine.start_kyc(
        user_id=_get_user_id(),
        level=body["level"],
    )


@router.post("/kyc/submit-document")
async def submit_document(body: dict):
    return _kyc_engine.submit_document(
        user_id=_get_user_id(),
        kyc_id=body["kyc_id"],
        document_type=body["document_type"],
        document_data=body.get("document_data", {}),
    )


@router.post("/kyc/verify-document/{document_id}")
async def verify_document(document_id: str, body: dict):
    return _kyc_engine.verify_document(
        document_type=body.get("document_type", ""),
        document_data=body.get("document_data", {}),
    )


@router.get("/kyc/status")
async def kyc_status():
    return _kyc_engine.check_kyc_status(_get_user_id())


@router.get("/kyc/required-documents")
async def required_documents(level: int = Query(...), country: str = Query(...)):
    return {"documents": _kyc_engine.get_required_documents(level, country)}


@router.get("/kyc/levels")
async def kyc_levels():
    return {"levels": _kyc_engine.get_kyc_levels()}


@router.get("/country-rules")
async def get_country_rules():
    return {"countries": compliance_router.get_all_countries()}


@router.get("/country-rules/{country_code}")
async def get_country_rules_by_code(country_code: str):
    return compliance_router.get_country_rules(country_code.upper())


@router.post("/check-transaction")
async def check_transaction(body: dict):
    return compliance_router.check_transaction(
        sender_country=body["sender_country"],
        recipient_country=body["recipient_country"],
        amount=body["amount"],
        currency=body.get("currency", "USD"),
        asset=body.get("asset", "fiat"),
    )


@router.get("/required-level")
async def required_kyc_level(
    country_code: str = Query(...),
    services: str = Query(""),
):
    return {
        "country_code": country_code,
        "required_kyc_level": compliance_router.get_required_kyc_level(
            country_code.upper(),
            [s.strip() for s in services.split(",") if s.strip()],
        ),
    }


@router.post("/reporting/sar")
async def generate_sar(body: dict):
    return _reporting_engine.generate_sar_report(body.get("data", body))


@router.post("/reporting/ctr")
async def generate_ctr(body: dict):
    return _reporting_engine.generate_ctr_report(body.get("data", body))


@router.post("/reporting/fbar")
async def generate_fbar(body: dict):
    return _reporting_engine.generate_fbar_report(body.get("data", body))


@router.post("/reporting/fatca")
async def generate_fatca(body: dict):
    return _reporting_engine.generate_fatca_report(body.get("data", body))


@router.post("/reporting/tax-report")
async def generate_tax_report(body: dict):
    return _reporting_engine.generate_tax_report(
        user_id=body.get("user_id", _get_user_id()),
        year=body.get("year", 2024),
    )


@router.get("/reporting/thresholds")
async def reporting_thresholds():
    return {"thresholds": _reporting_engine.get_reporting_thresholds()}


@router.get("/score")
async def compliance_score(user_id: str = Query("demo")):
    kyc_status = _kyc_engine.check_kyc_status(user_id)
    aml_history = _aml_engine.get_screening_history(user_id)
    sanctions_summary = _sanctions_engine.get_sanctions_summary()
    score = 85
    if kyc_status.get("status") == "verified":
        score += 10
    if len(aml_history) > 0:
        score -= 5
    return {
        "score": min(100, score),
        "kyc_status": kyc_status.get("status", "unknown"),
        "aml_checks": len(aml_history),
        "sanctions": sanctions_summary,
    }
