from fastapi import APIRouter, Query

from src.crypto import defi, staking, transactions, wallets

router = APIRouter(prefix="/api/v1/crypto")


def _get_user_id() -> str:
    return "demo"


@router.get("/wallets")
async def list_wallets():
    result = wallets.get_wallets(_get_user_id())
    return [w.to_dict() for w in result]


@router.post("/wallets")
async def create_wallet(currency: str, name: str, wallet_type: str = "hot"):
    wallet = wallets.create_wallet(_get_user_id(), currency, name, wallet_type)
    return wallet.to_dict()


@router.get("/wallets/{wallet_id}")
async def get_wallet(wallet_id: str):
    wallet = wallets.get_wallet(_get_user_id(), wallet_id)
    if wallet is None:
        return {"error": "Wallet not found"}
    return wallet.to_dict()


@router.get("/wallets/{wallet_id}/balance")
async def get_wallet_balance(wallet_id: str):
    return wallets.get_balance(_get_user_id(), wallet_id)


@router.get("/portfolio")
async def get_portfolio():
    return wallets.get_total_portfolio(_get_user_id())


@router.post("/wallets/multi-sig")
async def create_multi_sig_wallet(currency: str, signers: list[str], required_signatures: int):
    wallet = wallets.create_multi_sig_wallet(_get_user_id(), currency, signers, required_signatures)
    return wallet.to_dict()


@router.get("/wallets/{wallet_id}/deposit-address")
async def get_deposit_address(wallet_id: str):
    return wallets.generate_deposit_address(_get_user_id(), wallet_id)


@router.get("/transactions")
async def list_transactions(wallet_id: str | None = None, limit: int = Query(20, ge=1), offset: int = Query(0, ge=0)):
    return transactions.get_transactions(_get_user_id(), wallet_id=wallet_id, limit=limit, offset=offset)


@router.post("/transactions/send")
async def send_transaction(
    wallet_id: str,
    to_address: str,
    amount: float,
    currency: str,
    network: str,
    fee_level: str = "standard",
):
    tx = transactions.send_crypto(_get_user_id(), wallet_id, to_address, amount, currency, network, fee_level)
    return tx.to_dict()


@router.post("/transactions/swap")
async def swap_transaction(
    from_wallet: str,
    to_wallet: str,
    from_currency: str,
    to_currency: str,
    amount: float,
):
    swap = transactions.swap_crypto(_get_user_id(), from_wallet, to_wallet, from_currency, to_currency, amount)
    return swap.to_dict()


@router.get("/transactions/{tx_id}")
async def get_transaction(tx_id: str):
    tx = transactions.get_transaction(tx_id)
    if tx is None:
        return {"error": "Transaction not found"}
    return tx.to_dict()


@router.get("/fees/estimate")
async def estimate_fee(network: str, fee_level: str = "standard"):
    return transactions.estimate_fee(network, fee_level)


@router.post("/validate-address")
async def validate_address(address: str, currency: str):
    return transactions.validate_address(address, currency)


@router.get("/networks/{network}/status")
async def get_network_status(network: str):
    return transactions.get_network_status(network)


@router.get("/staking/rates")
async def get_staking_rates():
    return staking.get_staking_rates()


@router.get("/staking/validators")
async def get_validators(currency: str):
    return staking.get_validators(currency)


@router.post("/staking")
async def stake(wallet_id: str, amount: float, currency: str, validator: str):
    position = staking.stake(_get_user_id(), wallet_id, amount, currency, validator)
    return position.to_dict()


@router.get("/staking/positions")
async def list_staking_positions():
    result = staking.get_staking_positions(_get_user_id())
    return [p.to_dict() for p in result]


@router.get("/staking/positions/{stake_id}/rewards")
async def get_staking_rewards(stake_id: str):
    return staking.get_rewards(_get_user_id(), stake_id)


@router.post("/staking/positions/{stake_id}/claim")
async def claim_staking_rewards(stake_id: str):
    return staking.claim_rewards(_get_user_id(), stake_id)


@router.post("/staking/positions/{stake_id}/unstake")
async def unstake(stake_id: str):
    return staking.unstake(_get_user_id(), stake_id)


@router.post("/staking/calculate")
async def calculate_staking(amount: float, currency: str, duration_days: int):
    return staking.calculate_projected_rewards(amount, currency, duration_days)


@router.get("/defi/protocols")
async def list_defi_protocols():
    return defi.get_protocols()


@router.get("/defi/protocols/{protocol}/pools")
async def get_protocol_pools(protocol: str):
    return defi.get_liquidity_pools(protocol)


@router.get("/defi/yield-opportunities")
async def get_yield_opportunities(min_tvl: float = Query(0.0, ge=0), max_risk: str = "high"):
    return defi.get_yield_opportunities(min_tvl=min_tvl, max_risk=max_risk)


@router.post("/defi/quote")
async def get_defi_quote(from_token: str, to_token: str, amount: float, protocol: str = "1inch"):
    return defi.swap_quote(from_token, to_token, amount, protocol)


@router.get("/defi/positions")
async def get_defi_positions():
    result = defi.get_positions(_get_user_id())
    return [p.to_dict() for p in result]
