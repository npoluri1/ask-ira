from fastapi import APIRouter, Query

from src.payments import ach, engine, faster, rails, sepa, swift

router = APIRouter(prefix="/api/v1/payments")

# Seed demo data
engine.create_demo_data("demo")


def _resolve_user_id() -> str:
    return "demo"


@router.get("/")
async def list_payments(limit: int = Query(50, ge=1), offset: int = Query(0, ge=0)):
    return engine.get_payments(_resolve_user_id(), limit=limit, offset=offset)


@router.get("/{payment_id}")
async def get_payment(payment_id: str):
    return engine.get_payment(_resolve_user_id(), payment_id)


@router.get("/{payment_id}/status")
async def get_payment_status(payment_id: str):
    return engine.get_payment_status(_resolve_user_id(), payment_id)


@router.post("/")
async def create_payment(
    amount: float,
    currency: str,
    from_currency: str,
    to_currency: str,
    beneficiary: str,
    payment_type: str,
    description: str = "",
):
    return engine.create_payment(
        _resolve_user_id(), amount, currency, from_currency, to_currency,
        beneficiary, payment_type, description,
    )


@router.post("/{payment_id}/cancel")
async def cancel_payment(payment_id: str):
    return engine.cancel_payment(_resolve_user_id(), payment_id)


@router.get("/fees")
async def get_fees(amount: float, currency: str, payment_type: str):
    return engine.get_fees(amount, currency, payment_type)


@router.get("/estimated-delivery")
async def get_estimated_delivery(payment_type: str, from_currency: str = "", to_currency: str = ""):
    return engine.get_estimated_delivery(payment_type, from_currency, to_currency)


@router.get("/swift/member-banks")
async def get_swift_member_banks():
    return swift.get_participating_banks()


@router.post("/swift/mt103")
async def create_swift_mt103(
    sender_account: str,
    receiver_bic: str,
    receiver_account: str,
    amount: float,
    currency: str,
    beneficiary_name: str,
    beneficiary_address: str = "",
    intermediary_bic: str | None = None,
    purpose_code: str = "1000",
):
    return swift.create_mt103(
        _resolve_user_id(), sender_account, receiver_bic, receiver_account,
        amount, currency, beneficiary_name, beneficiary_address,
        intermediary_bic, purpose_code,
    )


@router.get("/swift/{swift_id}/track")
async def track_swift_message(swift_id: str):
    return swift.track_message(swift_id)


@router.post("/swift/validate-bic")
async def validate_bic(bic: str):
    return {"valid": swift.validate_bic(bic), "bic": bic}


@router.post("/swift/validate-iban")
async def validate_iban(iban: str):
    return {"valid": swift.validate_iban(iban), "iban": iban}


@router.post("/sepa/credit")
async def create_sepa_credit(
    from_iban: str,
    to_iban: str,
    amount: float,
    currency: str = "EUR",
    beneficiary_name: str = "",
    reference: str = "",
):
    return sepa.create_sepa_credit(
        _resolve_user_id(), from_iban, to_iban, amount, currency,
        beneficiary_name, reference,
    )


@router.post("/sepa/direct-debit")
async def create_sepa_direct_debit(
    mandate_id: str,
    from_iban: str,
    to_iban: str,
    amount: float,
    reference: str = "",
):
    return sepa.create_sepa_direct_debit(
        _resolve_user_id(), mandate_id, from_iban, to_iban, amount, "EUR", reference,
    )


@router.post("/sepa/mandate")
async def create_sepa_mandate(
    debtor_iban: str,
    debtor_name: str,
    creditor_name: str,
):
    return sepa.create_mandate(_resolve_user_id(), debtor_iban, debtor_name, creditor_name)


@router.get("/sepa/mandates")
async def list_sepa_mandates():
    return sepa.get_mandates(_resolve_user_id())


@router.post("/sepa/mandates/{mandate_id}/cancel")
async def cancel_sepa_mandate(mandate_id: str):
    return sepa.cancel_mandate(mandate_id)


@router.post("/ach/credit")
async def create_ach_credit(
    from_routing: str,
    from_account: str,
    to_routing: str,
    to_account: str,
    amount: float,
    description: str = "",
    company_name: str = "",
):
    return ach.create_ach_credit(
        _resolve_user_id(), from_routing, from_account, to_routing, to_account,
        amount, "USD", description, company_name,
    )


@router.post("/ach/debit")
async def create_ach_debit(
    from_routing: str,
    from_account: str,
    to_routing: str,
    to_account: str,
    amount: float,
    description: str = "",
):
    return ach.create_ach_debit(
        _resolve_user_id(), from_routing, from_account, to_routing, to_account,
        amount, "USD", description,
    )


@router.post("/ach/validate-routing")
async def validate_routing(routing_number: str):
    return {"valid": ach.validate_routing(routing_number), "routing_number": routing_number}


@router.get("/ach/sec-codes")
async def get_ach_sec_codes():
    return ach.get_ach_standard_entry_class_codes()


@router.get("/ach/settlement-timeline")
async def get_ach_settlement_timeline():
    return ach.get_settlement_timeline()


@router.post("/faster-payments")
async def create_faster_payment(
    from_account: str,
    to_account: str,
    sort_code: str,
    account_number: str,
    amount: float,
    reference: str = "",
):
    return faster.create_faster_payment(
        _resolve_user_id(), from_account, to_account, sort_code, account_number,
        amount, "GBP", reference,
    )


@router.post("/faster-payments/validate-sort-code")
async def validate_sort_code(sort_code: str):
    return {"valid": faster.validate_sort_code(sort_code), "sort_code": sort_code}


@router.get("/faster-payments/limits")
async def get_faster_payments_limits():
    return faster.get_limits()


@router.get("/rails")
async def list_rails():
    return rails.get_all_rails()


@router.post("/rails/best")
async def select_best_rail(source_currency: str, target_currency: str, amount: float, urgency: str = "standard"):
    return rails.select_best_rail(source_currency, target_currency, amount, urgency)


@router.post("/rails/optimize")
async def optimize_route(source_currency: str, target_currency: str, amount: float):
    return rails.calculate_optimized_route(source_currency, target_currency, amount)


@router.post("/rails/estimate-all")
async def estimate_all_rails(source_currency: str, target_currency: str, amount: float):
    return rails.estimate_all_rails(source_currency, target_currency, amount)
