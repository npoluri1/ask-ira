import pytest

from src.payments.ach import AHEngine
from src.payments.engine import SUPPORTED_PAYMENT_TYPES, PaymentsEngine
from src.payments.faster_payments import FasterPaymentsEngine
from src.payments.sepa import SEPAEngine
from src.payments.swift import IBAN_LENGTHS, SWIFT_MEMBER_BANKS, SWIFTEngine


@pytest.fixture
def engine():
    e = PaymentsEngine()
    e.create_demo_data("demo")
    return e


@pytest.mark.asyncio
async def test_create_payment(engine):
    payment = engine.create_payment(
        user_id="demo",
        amount=1000.0,
        currency="USD",
        from_currency="USD",
        to_currency="EUR",
        beneficiary="Test Beneficiary",
        payment_type="wire",
        description="Test payment",
    )
    assert payment["amount"] == 1000.0
    assert payment["currency"] == "USD"
    assert payment["payment_type"] == "wire"
    assert payment["status"] in ("pending", "processing")
    assert "payment_id" in payment


@pytest.mark.asyncio
async def test_create_payment_invalid_type(engine):
    with pytest.raises(ValueError):
        engine.create_payment(
            user_id="demo", amount=100, currency="USD",
            from_currency="USD", to_currency="USD",
            beneficiary="Test", payment_type="invalid_type",
        )


@pytest.mark.asyncio
async def test_get_payments(engine):
    payments = engine.get_payments("demo")
    assert len(payments) > 0


@pytest.mark.asyncio
async def test_get_payment_by_id(engine):
    payment = engine.create_payment(
        user_id="demo", amount=500, currency="USD",
        from_currency="USD", to_currency="USD",
        beneficiary="Test", payment_type="internal",
    )
    found = engine.get_payment("demo", payment["payment_id"])
    assert found is not None
    assert found["payment_id"] == payment["payment_id"]


@pytest.mark.asyncio
async def test_cancel_payment(engine):
    payment = engine.create_payment(
        user_id="demo", amount=200, currency="USD",
        from_currency="USD", to_currency="USD",
        beneficiary="Test", payment_type="internal",
    )
    cancelled = engine.cancel_payment("demo", payment["payment_id"])
    assert cancelled["status"] == "cancelled"


@pytest.mark.asyncio
async def test_get_fees(engine):
    fees = engine.get_fees(1000, "USD", "wire")
    assert "total_fee" in fees
    assert fees["currency"] == "USD"


@pytest.mark.asyncio
async def test_supported_payment_types():
    assert "wire" in SUPPORTED_PAYMENT_TYPES
    assert "swift" in SUPPORTED_PAYMENT_TYPES
    assert "sepa_credit" in SUPPORTED_PAYMENT_TYPES
    assert "ach_credit" in SUPPORTED_PAYMENT_TYPES


@pytest.mark.asyncio
async def test_swift_member_banks():
    assert len(SWIFT_MEMBER_BANKS) > 10
    bics = [b["bic"] for b in SWIFT_MEMBER_BANKS]
    assert "BOFAUS3N" in bics
    assert "DEUTDEFF" in bics


@pytest.mark.asyncio
async def test_swift_iban_validation():
    swift = SWIFTEngine()
    assert swift.validate_iban("GB82WEST12345698765432") is True
    assert swift.validate_iban("INVALID") is False


@pytest.mark.asyncio
async def test_iban_lengths():
    assert IBAN_LENGTHS["GB"] == 22
    assert IBAN_LENGTHS["DE"] == 22
    assert IBAN_LENGTHS["FR"] == 27


@pytest.mark.asyncio
async def test_swift_validate_bic():
    swift = SWIFTEngine()
    assert swift.validate_bic("BOFAUS3N") is True
    assert swift.validate_bic("INVALID") is False


@pytest.mark.asyncio
async def test_sepa_create_mandate():
    sepa = SEPAEngine()
    mandate = sepa.create_mandate(
        user_id="demo",
        debtor_iban="DE89370400440532013000",
        debtor_name="Demo User",
        creditor_name="Test Corp",
    )
    assert mandate["active"] is True
    assert mandate["creditor_name"] == "Test Corp"


@pytest.mark.asyncio
async def test_sepa_credit_transfer():
    sepa = SEPAEngine()
    transfer = sepa.create_sepa_credit(
        user_id="demo",
        amount=500.0,
        from_iban="DE89370400440532013000",
        to_iban="FR1420041010050500013M02606",
        beneficiary_name="Test Beneficiary",
    )
    assert transfer["amount"] == 500.0
    assert transfer["status"] == "completed"


@pytest.mark.asyncio
async def test_ach_create_credit():
    ach = AHEngine()
    result = ach.create_ach_credit(
        user_id="demo",
        from_routing="021000021",
        from_account="123456789",
        to_routing="021000021",
        to_account="987654321",
        amount=1000.0,
        description="Test ACH credit",
    )
    assert result["amount"] == 1000.0
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_faster_payments_limits():
    fp = FasterPaymentsEngine()
    limits = fp.get_limits()
    assert "max_single" in limits
    assert "max_daily" in limits
    assert limits["max_single"] <= limits["max_daily"]
