import pytest

from src.crypto.compliance import CryptoComplianceEngine
from src.crypto.defi import DeFiEngine
from src.crypto.staking import StakingEngine
from src.crypto.transactions import CryptoTransactionsEngine
from src.crypto.wallets import SUPPORTED_CURRENCIES, CryptoWalletEngine, Wallet


@pytest.fixture(autouse=True)
def reset_class_dbs():
    original_wallets = CryptoWalletEngine.WALLETS_DB.copy()
    original_multisig = CryptoWalletEngine.MULTI_SIG_DB.copy()
    yield
    CryptoWalletEngine.WALLETS_DB = original_wallets
    CryptoWalletEngine.MULTI_SIG_DB = original_multisig


@pytest.fixture
def wallet_engine():
    CryptoWalletEngine.WALLETS_DB = {}
    CryptoWalletEngine.MULTI_SIG_DB = {}
    CryptoWalletEngine._address_index = {}
    return CryptoWalletEngine()


@pytest.fixture
def tx_engine():
    engine = CryptoTransactionsEngine()
    engine.TX_DB = {}
    engine.SWAP_DB = {}
    return engine


@pytest.fixture
def staking_engine():
    engine = StakingEngine()
    engine.STAKING_DB = {}
    return engine


@pytest.fixture
def defi_engine():
    engine = DeFiEngine()
    engine.POSITIONS_DB = {}
    return engine


@pytest.fixture
def compliance_engine():
    return CryptoComplianceEngine()


@pytest.mark.asyncio
async def test_create_wallet(wallet_engine):
    wallet = wallet_engine.create_wallet(
        user_id="user1",
        currency="BTC",
        name="My Bitcoin Wallet",
    )
    assert isinstance(wallet, Wallet)
    wallet_dict = wallet.to_dict()
    assert wallet_dict["currency"] == "BTC"
    assert wallet_dict["balance"] == 0.0
    assert wallet_dict["name"] == "My Bitcoin Wallet"
    assert wallet_dict["address"].startswith("1")


@pytest.mark.asyncio
async def test_create_wallet_invalid_currency(wallet_engine):
    with pytest.raises(ValueError):
        wallet_engine.create_wallet("user1", "INVALID_COIN", name="Test Wallet")


@pytest.mark.asyncio
async def test_get_wallets(wallet_engine):
    wallet_engine.create_wallet("user2", "ETH", name="ETH Wallet")
    wallet_engine.create_wallet("user2", "SOL", name="SOL Wallet")
    wallets = wallet_engine.get_wallets("user2")
    assert len(wallets) == 2
    currencies = {w.currency for w in wallets}
    assert currencies == {"ETH", "SOL"}


@pytest.mark.asyncio
async def test_supported_currencies():
    assert "BTC" in SUPPORTED_CURRENCIES
    assert "ETH" in SUPPORTED_CURRENCIES
    assert "SOL" in SUPPORTED_CURRENCIES


@pytest.mark.asyncio
async def test_create_transaction(tx_engine, wallet_engine):
    wallet = wallet_engine.create_wallet("user1", "BTC", name="BTC Wallet")
    wallet.balance = 10.0

    tx = tx_engine.send_crypto(
        user_id="user1",
        wallet_id=wallet.wallet_id,
        to_address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        amount=0.5,
        currency="BTC",
        network="bitcoin",
    )
    tx_dict = tx.to_dict()
    assert tx_dict["currency"] == "BTC"
    assert tx_dict["amount"] == 0.5
    assert tx_dict["status"] == "confirmed"


@pytest.mark.asyncio
async def test_get_transactions(tx_engine, wallet_engine):
    wallet = wallet_engine.create_wallet("user1", "BTC", name="BTC Wallet")
    wallet.balance = 10.0

    tx_engine.send_crypto("user1", wallet.wallet_id, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0.5, "BTC", "bitcoin")
    result = tx_engine.get_transactions("user1")
    assert "transactions" in result
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_create_staking(staking_engine, wallet_engine):
    wallet = wallet_engine.create_wallet("user1", "SOL", name="SOL Wallet")
    wallet.balance = 200.0

    stake = staking_engine.stake(
        user_id="user1",
        wallet_id=wallet.wallet_id,
        currency="SOL",
        amount=100.0,
        validator="Jito",
    )
    stake_dict = stake.to_dict()
    assert stake_dict["currency"] == "SOL"
    assert stake_dict["amount"] == 100.0
    assert stake_dict["status"] == "active"
    assert "apy" in stake_dict
    assert "rewards" in stake_dict


@pytest.mark.asyncio
async def test_create_defi_position(defi_engine):
    pos = defi_engine.provide_liquidity(
        user_id="user1",
        protocol="uniswap_v3",
        pool="ETH/USDC",
        amount0=2.0,
        amount1=5000.0,
        token0="ETH",
        token1="USDC",
    )
    pos_dict = pos.to_dict()
    assert pos_dict["protocol"] == "uniswap_v3"
    assert pos_dict["status"] == "active"
    assert "position_id" in pos_dict


@pytest.mark.asyncio
async def test_crypto_compliance_screen(compliance_engine):
    result = compliance_engine.screen_transaction({
        "from": "0xFROM",
        "to": "0xTO",
        "amount": 50000.0,
        "currency": "USDT",
        "network": "erc20",
    })
    assert "risk_score" in result
    assert "flags" in result
