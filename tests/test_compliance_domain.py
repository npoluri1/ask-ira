import pytest

from src.compliance.aml import HIGH_RISK_COUNTRIES, AMLEngine
from src.compliance.kyc import KYC_LEVELS, KYCEngine
from src.compliance.reporting import ReportingEngine
from src.compliance.sanctions import SanctionsEngine


@pytest.mark.asyncio
async def test_aml_screen_user_clean():
    aml = AMLEngine()
    result = aml.screen_user(
        user_id="u1",
        name="John Doe",
        date_of_birth="1990-01-01",
        nationality="US",
        country_of_residence="US",
    )
    assert "risk_score" in result
    assert "flags" in result
    assert "risk_level" in result


@pytest.mark.asyncio
async def test_aml_screen_user_pep():
    aml = AMLEngine()
    result = aml.screen_user(
        user_id="u2",
        name="Vladimir Petrov",
        date_of_birth="1970-05-15",
        nationality="RU",
        country_of_residence="RU",
    )
    assert result["risk_score"] >= 40
    assert any("PEP" in f for f in result["flags"])


@pytest.mark.asyncio
async def test_aml_screen_user_high_risk_country():
    aml = AMLEngine()
    result = aml.screen_user(
        user_id="u3",
        name="Test User",
        date_of_birth="1980-01-01",
        nationality="Iran",
        country_of_residence="Iran",
    )
    assert result["risk_score"] >= 25


@pytest.mark.asyncio
async def test_aml_screen_transaction():
    aml = AMLEngine()
    result = aml.screen_transaction(
        user_id="u1",
        amount=15000.0,
        currency="USD",
        counterparty="Offshore Ltd",
        country="IR",
    )
    assert "decision" in result
    assert "flags" in result


@pytest.mark.asyncio
async def test_aml_check_structuring():
    aml = AMLEngine()
    transactions = [
        {"user_id": "u1", "amount": 9000, "timestamp": "2026-05-12T10:00:00Z"},
        {"user_id": "u1", "amount": 8500, "timestamp": "2026-05-12T12:00:00Z"},
        {"user_id": "u1", "amount": 9500, "timestamp": "2026-05-12T14:00:00Z"},
    ]
    result = aml.check_structuring(transactions)
    assert len(result) > 0
    assert result[0]["type"] == "structuring_alert"


@pytest.mark.asyncio
async def test_high_risk_countries():
    assert "Iran" in HIGH_RISK_COUNTRIES
    assert "North Korea" in HIGH_RISK_COUNTRIES


@pytest.mark.asyncio
async def test_kyc_levels():
    assert KYC_LEVELS[1]["name"] == "Basic"
    assert KYC_LEVELS[2]["name"] == "Standard"
    assert KYC_LEVELS[3]["name"] == "Advanced"
    assert KYC_LEVELS[4]["name"] == "Institutional"


@pytest.mark.asyncio
async def test_kyc_start_verification():
    kyc = KYCEngine()
    result = kyc.start_kyc(
        user_id="u1",
        level=2,
    )
    assert result["status"] == "pending"
    assert "kyc_id" in result
    assert result["total_required_documents"] > 0


@pytest.mark.asyncio
async def test_kyc_submit_document():
    kyc = KYCEngine()
    verification = kyc.start_kyc(user_id="u1", level=2)
    result = kyc.submit_document(
        user_id="u1",
        kyc_id=verification["kyc_id"],
        document_type="passport",
        document_data={"document_number": "AB123456"},
    )
    assert result["verification_status"] in ("verified", "rejected")


@pytest.mark.asyncio
async def test_sanctions_check_name():
    sanctions = SanctionsEngine()
    result = sanctions.check_name("Ivan Kozlov")
    assert len(result) > 0
    assert any(m["matched_entry"]["name"] == "Ivan Kozlov" for m in result)


@pytest.mark.asyncio
async def test_sanctions_check_name_clean():
    sanctions = SanctionsEngine()
    result = sanctions.check_name("John Smith")
    assert len(result) == 0


@pytest.mark.asyncio
async def test_sanctions_check_country():
    sanctions = SanctionsEngine()
    result = sanctions.check_country("Iran")
    assert result["restricted"] is True


@pytest.mark.asyncio
async def test_reporting_file_sar():
    reporting = ReportingEngine()
    result = reporting.generate_sar_report(
        {
            "subject_name": "John Doe",
            "user_id": "u1",
            "amount": 25000,
            "currency": "USD",
            "counterparty": "Suspicious Entity",
            "transaction_date": "2026-05-12",
            "reason": "Suspicious transaction pattern",
            "narrative": "Multiple near-threshold transactions",
            "evidence": ["Transaction logs"],
            "regulatory_body": "FinCEN",
        }
    )
    assert result["status"] == "submitted"
    assert "report_id" in result
