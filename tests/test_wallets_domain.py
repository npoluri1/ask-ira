import pytest
from src.wallets.banking_wallet import BankingWalletEngine
from src.wallets.crypto_wallet import CryptoWalletEngine
from src.wallets.insurance_wallet import InsuranceWalletEngine


@pytest.mark.asyncio
async def test_create_banking_wallet():
    engine = BankingWalletEngine()
    wallet = engine.create_banking_wallet(
        user_id="user1",
        currency="USD",
        wallet_name="Main Wallet",
        features=["multi_currency", "virtual_iban"],
    )
    assert wallet["currency"] == "USD"
    assert wallet["wallet_name"] == "Main Wallet"
    assert wallet["main_balance"] == 0.0
    assert "wallet_id" in wallet


@pytest.mark.asyncio
async def test_get_banking_wallets():
    engine = BankingWalletEngine()
    engine.create_banking_wallet("user2", "EUR", "Euro Wallet")
    engine.create_banking_wallet("user2", "GBP", "Pound Wallet")
    wallets = engine.get_wallets("user2")
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_create_virtual_iban():
    engine = BankingWalletEngine()
    wallet = engine.create_banking_wallet("user3", "USD", "IBAN Wallet", ["virtual_iban"])
    iban = engine.create_virtual_iban(wallet["wallet_id"], "DE")
    assert iban["country"] == "DE"
    assert iban["iban"].startswith("DE")


@pytest.mark.asyncio
async def test_create_crypto_wallet():
    engine = CryptoWalletEngine()
    engine.create_demo_data("user1")
    balances = engine.get_all_crypto_balances("user1")
    assert "user_id" in balances
    assert balances["user_id"] == "user1"
    assert "BTC" in balances["balances"]


@pytest.mark.asyncio
async def test_get_crypto_wallets():
    engine = CryptoWalletEngine()
    engine.create_demo_data("user2")
    balances = engine.get_all_crypto_balances("user2")
    assert len(balances["balances"]) >= 2
    assert balances["total_value_usd"] > 0


@pytest.mark.asyncio
async def test_create_insurance_wallet():
    engine = InsuranceWalletEngine()
    wallet = engine.create_insurance_wallet(
        user_id="user1",
        wallet_name="Life Insurance Fund",
    )
    assert wallet["wallet_name"] == "Life Insurance Fund"
    assert wallet["total_premiums_paid"] == 0.0
    assert "wallet_id" in wallet


@pytest.mark.asyncio
async def test_get_insurance_wallet_balance():
    engine = InsuranceWalletEngine()
    wallet = engine.create_insurance_wallet("user2", "Health Fund")
    result = engine.get_wallet("user2", wallet["wallet_id"])
    assert result is not None
    assert "total_premiums_paid" in result
    assert "status" in result
