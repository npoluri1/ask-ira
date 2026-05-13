from fastapi import APIRouter, Query

from src.wallets import banking, crypto_wallet, insurance

router = APIRouter(prefix="/api/v1/wallets")

_banking_engine = banking
_insurance_engine = insurance
_crypto_engine = crypto_wallet.CryptoWalletEngine()

# Seed demo data
_banking_engine.create_demo_data("demo")


def _get_user_id() -> str:
    return "demo"


@router.get("/banking")
async def list_banking_wallets():
    return {"wallets": _banking_engine.get_wallets(_get_user_id())}


@router.post("/banking")
async def create_banking_wallet(body: dict):
    return _banking_engine.create_banking_wallet(
        user_id=_get_user_id(),
        currency=body.get("currency", "USD"),
        wallet_name=body.get("wallet_name", ""),
        features=body.get("features", []),
    )


@router.get("/banking/summary")
async def banking_summary():
    return _banking_engine.get_total_balance(_get_user_id())


@router.get("/banking/{wallet_id}")
async def get_banking_wallet(wallet_id: str):
    wallet = _banking_engine.get_wallet(_get_user_id(), wallet_id)
    if not wallet:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Wallet not found"})
    return wallet


@router.post("/banking/{wallet_id}/virtual-iban")
async def generate_virtual_iban(wallet_id: str, body: dict):
    return _banking_engine.create_virtual_iban(wallet_id, body.get("country", "US"))


@router.post("/banking/{wallet_id}/spending-rules")
async def set_spending_rules(wallet_id: str, body: dict):
    return _banking_engine.set_spending_rules(
        user_id=_get_user_id(),
        wallet_id=wallet_id,
        rules=body.get("rules", body),
    )


@router.post("/banking/{wallet_id}/auto-save")
async def set_auto_save(wallet_id: str, body: dict):
    return _banking_engine.set_auto_save_rule(
        user_id=_get_user_id(),
        wallet_id=wallet_id,
        rule=body.get("rule", body),
    )


@router.post("/banking/{wallet_id}/link-open-banking")
async def link_open_banking(wallet_id: str, body: dict):
    return _banking_engine.link_open_banking(
        user_id=_get_user_id(),
        wallet_id=wallet_id,
        provider=body["provider"],
        external_account_id=body["external_account_id"],
    )


@router.get("/banking/aggregated")
async def aggregated_balances():
    return _banking_engine.get_aggregated_balances(_get_user_id())


@router.get("/banking/{wallet_id}/analytics")
async def spending_analytics(wallet_id: str, period: str = Query("monthly")):
    return _banking_engine.get_spending_analytics(
        user_id=_get_user_id(),
        wallet_id=wallet_id,
        period=period,
    )


@router.get("/insurance")
async def list_insurance_wallets():
    return {"wallets": _insurance_engine.get_wallets(_get_user_id())}


@router.post("/insurance")
async def create_insurance_wallet(body: dict):
    return _insurance_engine.create_insurance_wallet(
        user_id=_get_user_id(),
        wallet_name=body.get("wallet_name", ""),
    )


@router.get("/insurance/{wallet_id}")
async def get_insurance_wallet(wallet_id: str):
    wallet = _insurance_engine.get_wallet(_get_user_id(), wallet_id)
    if not wallet:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Wallet not found"})
    return wallet


@router.get("/insurance/{wallet_id}/premiums")
async def insurance_premiums(wallet_id: str):
    return _insurance_engine.track_premiums(_get_user_id(), wallet_id)


@router.get("/insurance/{wallet_id}/claims")
async def insurance_claims(wallet_id: str):
    return _insurance_engine.track_claims(_get_user_id(), wallet_id)


@router.get("/insurance/{wallet_id}/cash-value")
async def insurance_cash_value(wallet_id: str):
    return _insurance_engine.get_cash_value(_get_user_id(), wallet_id)


@router.get("/insurance/{wallet_id}/coverage")
async def insurance_coverage(wallet_id: str):
    return _insurance_engine.get_policy_coverage_summary(_get_user_id(), wallet_id)


@router.get("/crypto")
async def crypto_balances():
    return _crypto_engine.get_all_crypto_balances(_get_user_id())


@router.get("/crypto/value")
async def crypto_total_value():
    return _crypto_engine.get_total_crypto_value_usd(_get_user_id())


@router.get("/crypto/allocation")
async def crypto_allocation():
    return _crypto_engine.get_portfolio_allocation(_get_user_id())


@router.get("/crypto/staking")
async def crypto_staking():
    return _crypto_engine.stake_summary(_get_user_id())


@router.get("/crypto/defi")
async def crypto_defi():
    return _crypto_engine.defi_summary(_get_user_id())


@router.get("/crypto/transactions")
async def crypto_transactions(limit: int = Query(10)):
    return {"transactions": _crypto_engine.transaction_history(_get_user_id(), limit)}
