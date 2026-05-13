import pytest

from src.products.annuities import AnnuitiesEngine
from src.products.fixed_deposits import FixedDepositsEngine
from src.products.mutual_funds import MutualFundsEngine
from src.products.sip import SIPEngine


@pytest.mark.asyncio
async def test_create_mutual_fund():
    engine = MutualFundsEngine()
    fund = engine.buy_fund(
        user_id="user1",
        fund_id="VFIAX",
        amount=10000,
    )
    assert fund["fund_name"] == "Vanguard 500 Index Fund Admiral"
    assert fund["fund_id"] == "VFIAX"
    assert fund["invested_amount"] == 10000


@pytest.mark.asyncio
async def test_get_mutual_funds():
    engine = MutualFundsEngine()
    engine.buy_fund("user2", "VFIAX", 5000)
    funds = engine.get_holdings("user2")
    assert len(funds) >= 1


@pytest.mark.asyncio
async def test_create_mutual_fund_invalid_type():
    engine = MutualFundsEngine()
    with pytest.raises(ValueError):
        engine.buy_fund("user1", "INVALID", 10000)


@pytest.mark.asyncio
async def test_create_fixed_deposit():
    engine = FixedDepositsEngine()
    deposit = engine.open_fd(
        user_id="user1",
        product_id="fd_1y",
        amount=25000,
    )
    assert deposit["principal"] == 25000
    assert deposit["term_days"] == 365
    assert deposit["maturity_amount"] > deposit["principal"]


@pytest.mark.asyncio
async def test_get_fixed_deposits():
    engine = FixedDepositsEngine()
    engine.open_fd("user2", "fd_1y", 10000)
    deposits = engine.get_holdings("user2")
    assert len(deposits) >= 1


@pytest.mark.asyncio
async def test_create_annuity():
    engine = AnnuitiesEngine()
    annuity = engine.purchase(
        user_id="user1",
        annuity_type="immediate_fixed",
        investment=100000,
    )
    assert annuity["annuity_type"] == "immediate_fixed"
    assert annuity["investment"] == 100000
    assert annuity["status"] == "active"


@pytest.mark.asyncio
async def test_create_sip():
    engine = SIPEngine()
    sip = engine.start_sip(
        user_id="user1",
        fund_id="VFIAX",
        monthly_amount=5000,
        frequency="monthly",
    )
    assert sip["monthly_amount"] == 5000
    assert sip["frequency"] == "monthly"
    assert sip["status"] == "active"
