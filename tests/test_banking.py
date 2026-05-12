import pytest
from src.banking.accounts import AccountsEngine
from src.banking.transfers import TransfersEngine
from src.banking.loans import LoansEngine
from src.banking.deposits import DepositsEngine
from src.banking.credit_cards import CreditCardsEngine
from src.banking.bills import BillsEngine


@pytest.fixture
def accounts_engine():
    return AccountsEngine()


@pytest.fixture
def transfers_engine():
    return TransfersEngine()


@pytest.fixture
def loans_engine():
    return LoansEngine()


@pytest.fixture
def deposits_engine():
    return DepositsEngine()


@pytest.fixture
def cards_engine():
    return CreditCardsEngine()


@pytest.fixture
def bills_engine():
    return BillsEngine()


@pytest.mark.asyncio
async def test_create_account(accounts_engine):
    acct = accounts_engine.create_account("user1", "checking", "USD", 1000)
    assert acct["user_id"] == "user1"
    assert acct["type"] == "checking"
    assert acct["balance"] == 1000
    assert acct["status"] == "active"
    assert acct["account_id"].startswith("IRA")


@pytest.mark.asyncio
async def test_create_account_invalid_type(accounts_engine):
    with pytest.raises(ValueError):
        accounts_engine.create_account("user1", "invalid_type")


@pytest.mark.asyncio
async def test_get_accounts(accounts_engine):
    accounts_engine.create_account("user2", "savings", "USD", 500)
    accts = accounts_engine.get_accounts("user2")
    assert len(accts) >= 1
    assert accts[0]["type"] == "savings"


@pytest.mark.asyncio
async def test_get_account(accounts_engine):
    acct = accounts_engine.create_account("user3", "money_market", "USD", 2000)
    found = accounts_engine.get_account("user3", acct["account_id"])
    assert found is not None
    assert found["balance"] == 2000


@pytest.mark.asyncio
async def test_close_account(accounts_engine):
    acct = accounts_engine.create_account("user4", "checking")
    result = accounts_engine.close_account("user4", acct["account_id"])
    assert result["status"] == "closed"
    assert result["closed_at"] is not None


@pytest.mark.asyncio
async def test_create_savings_account_interest(accounts_engine):
    acct = accounts_engine.create_account("user5", "savings", "USD", 10000)
    assert acct["interest_rate"] == 0.045


@pytest.mark.asyncio
async def test_create_transfer(accounts_engine, transfers_engine):
    src = accounts_engine.create_account("user1", "checking", "USD", 1000)
    dst = accounts_engine.create_account("user1", "savings", "USD", 500)
    transfer = transfers_engine.initiate_transfer(
        user_id="user1",
        from_account=src["account_id"],
        to_account=dst["account_id"],
        amount=500.0,
        transfer_type="internal",
    )
    assert transfer["amount"] == 500.0
    assert transfer["transfer_type"] == "internal"
    assert transfer["status"] == "completed"


@pytest.mark.asyncio
async def test_create_transfer_exceeds_balance(accounts_engine, transfers_engine):
    src = accounts_engine.create_account("user1", "checking", "USD", 500)
    dst = accounts_engine.create_account("user1", "savings", "USD", 0)
    with pytest.raises(ValueError, match="Insufficient funds"):
        transfers_engine.initiate_transfer(
            user_id="user1",
            from_account=src["account_id"],
            to_account=dst["account_id"],
            amount=1_000_000.0,
            transfer_type="internal",
        )


@pytest.mark.asyncio
async def test_create_loan(loans_engine):
    loan = loans_engine.apply_loan(
        user_id="user1",
        loan_type="personal",
        amount=10000,
        term_months=12,
    )
    assert loan["principal"] == 10000
    assert loan["status"] == "approved"
    assert loan["term_months"] == 12
    assert "annual_rate" in loan
    assert "emi" in loan


@pytest.mark.asyncio
async def test_create_deposit(deposits_engine):
    dep = deposits_engine.open_deposit(
        user_id="user1",
        product_id="fixed_deposit",
        amount=5000,
    )
    assert dep["amount"] == 5000
    assert dep["status"] == "active"
    matured = deposits_engine.get_matured_value(dep["deposit_id"], "user1")
    assert matured["matured_value"] > dep["amount"]


@pytest.mark.asyncio
async def test_create_credit_card(cards_engine):
    card = cards_engine.apply_card(
        user_id="user1",
        product_id="cashback",
    )
    assert card["credit_limit"] > 0
    assert card["status"] == "active"
    assert "card_id" in card


@pytest.mark.asyncio
async def test_create_bill(bills_engine):
    bill = bills_engine.add_bill(
        user_id="user1",
        biller_name="Electric Co",
        category="utilities",
        amount=150.0,
        due_day=1,
    )
    assert bill["amount"] == 150.0
    assert bill["status"] == "active"
    assert bill["biller_name"] == "Electric Co"
