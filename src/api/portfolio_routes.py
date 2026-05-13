from fastapi import APIRouter

from src.portfolio import calculate_portfolio, get_diversification_score, rebalance_portfolio
from src.products import annuities, fixed_deposits, mutual_funds, sip
from src.trade_execution import (
    approve_trade,
    execute_trade,
    get_balance,
    get_pending_approvals,
    get_trade_history,
)

router = APIRouter(prefix="/api/v1/portfolio")


def _get_user_id() -> str:
    return "demo"


@router.get("/")
async def get_portfolio():
    return calculate_portfolio(_get_user_id())


@router.post("/rebalance")
async def rebalance(body: dict):
    return rebalance_portfolio(
        user_id=_get_user_id(),
        target_allocations=body["target_allocations"],
    )


@router.get("/diversification")
async def diversification():
    portfolio = calculate_portfolio(_get_user_id())
    return get_diversification_score(portfolio)


@router.get("/balance")
async def account_balance():
    return get_balance(_get_user_id())


@router.get("/trades")
async def trade_history():
    return {"trades": get_trade_history(_get_user_id())}


@router.post("/trades")
async def execute_trade_endpoint(body: dict):
    return execute_trade(
        user_id=_get_user_id(),
        symbol=body["symbol"],
        side=body["side"],
        quantity=body["quantity"],
        order_type=body.get("order_type", "market"),
    )


@router.get("/approvals")
async def pending_approvals():
    return {"pending_approvals": get_pending_approvals(_get_user_id())}


@router.post("/approvals/{approval_id}")
async def approve_trade_endpoint(approval_id: str):
    return approve_trade(approval_id=approval_id, user_id=_get_user_id())


@router.get("/mutual-funds")
async def list_mutual_funds():
    return {"funds": mutual_funds.get_funds()}


@router.get("/mutual-funds/{fund_id}")
async def get_mutual_fund(fund_id: str):
    fund = mutual_funds.get_fund(fund_id)
    if not fund:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Fund not found"})
    return fund


@router.post("/mutual-funds/buy")
async def buy_mutual_fund(body: dict):
    return mutual_funds.buy_fund(
        user_id=_get_user_id(),
        fund_id=body["fund_id"],
        amount=body["amount"],
    )


@router.get("/mutual-funds/holdings")
async def mutual_fund_holdings():
    return {"holdings": mutual_funds.get_holdings(_get_user_id())}


@router.get("/mutual-funds/summary")
async def mutual_fund_summary():
    return mutual_funds.get_portfolio_summary(_get_user_id())


@router.get("/fixed-deposits/products")
async def fd_products():
    return {"products": fixed_deposits.get_products()}


@router.get("/fixed-deposits/products/{product_id}")
async def fd_product(product_id: str):
    product = fixed_deposits.get_product(product_id)
    if not product:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    return product


@router.post("/fixed-deposits/calculate")
async def fd_calculate(body: dict):
    return fixed_deposits.calculate_maturity(
        product_id=body["product_id"],
        amount=body["amount"],
    )


@router.post("/fixed-deposits/open")
async def fd_open(body: dict):
    return fixed_deposits.open_fd(
        user_id=_get_user_id(),
        product_id=body["product_id"],
        amount=body["amount"],
    )


@router.get("/fixed-deposits")
async def fd_holdings():
    return {"holdings": fixed_deposits.get_holdings(_get_user_id())}


@router.post("/fixed-deposits/{fd_id}/close")
async def fd_close(fd_id: str):
    return fixed_deposits.close_fd(user_id=_get_user_id(), fd_id=fd_id)


@router.get("/annuities/products")
async def annuity_products():
    return {"products": annuities.get_products()}


@router.post("/annuities/calculate")
async def annuity_calculate(body: dict):
    return annuities.calculate_payout(
        annuity_type=body["annuity_type"],
        investment=body["investment"],
        payout_option=body.get("payout_option", "life_only"),
        age=body.get("age", 65),
        term_years=body.get("term_years"),
    )


@router.post("/annuities/purchase")
async def annuity_purchase(body: dict):
    return annuities.purchase(
        user_id=_get_user_id(),
        annuity_type=body["annuity_type"],
        investment=body["investment"],
        payout_option=body.get("payout_option", "life_only"),
        age=body.get("age", 60),
        deferral_years=body.get("deferral_years", 10),
    )


@router.get("/annuities/holdings")
async def annuity_holdings():
    return {"holdings": annuities.get_holdings(_get_user_id())}


@router.get("/annuities/summary")
async def annuity_summary():
    return annuities.get_portfolio_summary(_get_user_id())


@router.get("/sip/funds")
async def sip_funds():
    return {"funds": sip.get_sip_funds()}


@router.post("/sip/calculate")
async def sip_calculate(body: dict):
    return sip.calculate_sip(
        monthly_amount=body["monthly_amount"],
        expected_return=body.get("expected_return", 0.12),
        years=body.get("years", 10),
    )


@router.post("/sip/start")
async def sip_start(body: dict):
    return sip.start_sip(
        user_id=_get_user_id(),
        fund_id=body["fund_id"],
        monthly_amount=body["monthly_amount"],
        frequency=body.get("frequency", "monthly"),
    )


@router.get("/sip")
async def sip_list():
    return {"sips": sip.get_sips(_get_user_id())}


@router.post("/sip/{sip_id}/stop")
async def sip_stop(sip_id: str):
    return sip.stop_sip(user_id=_get_user_id(), sip_id=sip_id)


@router.get("/sip/summary")
async def sip_summary():
    return sip.get_portfolio_summary(_get_user_id())
