import time
import uuid
from typing import Any

CRYPTO_WALLETS_DB: dict[str, dict[str, Any]] = {}

CRYPTO_CURRENCIES: list[str] = ["BTC", "ETH", "SOL", "USDT", "USDC", "ADA", "DOT", "AVAX", "LINK", "MATIC"]

PRICES_USD: dict[str, float] = {
    "BTC": 67500.0, "ETH": 3450.0, "SOL": 145.0, "USDT": 1.0, "USDC": 1.0,
    "ADA": 0.45, "DOT": 7.20, "AVAX": 35.0, "LINK": 14.50, "MATIC": 0.55,
}

STAKING_PROTOCOLS: list[str] = ["Ethereum 2.0", "Solana", "Cardano", "Polkadot", "Avalanche"]
DEFI_PROTOCOLS: list[str] = ["Aave", "Uniswap", "Curve", "Compound", "Lido", "MakerDAO"]


class CryptoWalletEngine:
    def get_all_crypto_balances(self, user_id: str) -> dict[str, Any]:
        wallet = CRYPTO_WALLETS_DB.get(user_id)
        if not wallet:
            return {"user_id": user_id, "balances": {}, "total_value_usd": 0.0}

        balances: dict[str, dict[str, Any]] = {}
        total = 0.0
        for symbol, amount in wallet.get("balances", {}).items():
            price = PRICES_USD.get(symbol, 0)
            value = round(amount * price, 2)
            balances[symbol] = {
                "balance": amount,
                "price_usd": price,
                "value_usd": value,
                "changes_24h_pct": round((price * 0.02) / price * 100, 2) if price else 0,
            }
            total += value

        return {
            "user_id": user_id,
            "balances": balances,
            "total_value_usd": round(total, 2),
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def get_total_crypto_value_usd(self, user_id: str) -> dict[str, Any]:
        wallet = CRYPTO_WALLETS_DB.get(user_id)
        if not wallet:
            return {"user_id": user_id, "total_value_usd": 0.0, "currency": "USD"}

        total = 0.0
        for symbol, amount in wallet.get("balances", {}).items():
            total += amount * PRICES_USD.get(symbol, 0)

        return {
            "user_id": user_id,
            "total_value_usd": round(total, 2),
            "currency": "USD",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "breakdown": {sym: round(amt * PRICES_USD.get(sym, 0), 2) for sym, amt in wallet.get("balances", {}).items()},
        }

    def get_portfolio_allocation(self, user_id: str) -> dict[str, Any]:
        wallet = CRYPTO_WALLETS_DB.get(user_id)
        if not wallet or not wallet.get("balances"):
            return {"user_id": user_id, "allocations": {}, "total_value_usd": 0.0}

        total = 0.0
        values: dict[str, float] = {}
        for symbol, amount in wallet["balances"].items():
            value = amount * PRICES_USD.get(symbol, 0)
            values[symbol] = value
            total += value

        allocations: dict[str, dict[str, Any]] = {}
        for symbol, value in values.items():
            allocations[symbol] = {
                "balance": wallet["balances"][symbol],
                "value_usd": round(value, 2),
                "allocation_pct": round((value / total * 100) if total else 0, 2),
            }

        return {
            "user_id": user_id,
            "allocations": allocations,
            "total_value_usd": round(total, 2),
            "diversification_score": round(min(len(allocations) / 5 * 100, 100), 1),
            "largest_position": max(allocations, key=lambda s: allocations[s]["value_usd"]) if allocations else None,
        }

    def stake_summary(self, user_id: str) -> dict[str, Any]:
        wallet = CRYPTO_WALLETS_DB.get(user_id)
        staked = wallet.get("staking_positions", []) if wallet else []

        total_staked_value = 0.0
        for pos in staked:
            total_staked_value += pos.get("amount", 0) * PRICES_USD.get(pos.get("currency", "ETH"), 0)

        return {
            "user_id": user_id,
            "staking_positions": staked,
            "total_staked_value_usd": round(total_staked_value, 2),
            "active_validators": len(staked),
            "average_apr": round(sum(p.get("apr", 0) for p in staked) / len(staked), 2) if staked else 0,
            "total_rewards_earned": round(sum(p.get("rewards_earned", 0) * PRICES_USD.get(p.get("currency", "ETH"), 0) for p in staked), 2),
        }

    def defi_summary(self, user_id: str) -> dict[str, Any]:
        wallet = CRYPTO_WALLETS_DB.get(user_id)
        defi = wallet.get("defi_positions", []) if wallet else []

        total_defi_value = 0.0
        for pos in defi:
            total_defi_value += pos.get("deposited_value_usd", 0)

        return {
            "user_id": user_id,
            "defi_positions": defi,
            "total_defi_value_usd": round(total_defi_value, 2),
            "active_protocols": len(set(p.get("protocol", "") for p in defi)),
            "total_earned_yield_usd": round(sum(p.get("yield_earned_usd", 0) for p in defi), 2),
            "average_apy": round(sum(p.get("apy", 0) for p in defi) / len(defi), 2) if defi else 0,
        }

    def transaction_history(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        wallet = CRYPTO_WALLETS_DB.get(user_id)
        if not wallet:
            return []

        txns = sorted(wallet.get("transactions", []), key=lambda t: t.get("timestamp", ""), reverse=True)
        return txns[:limit]

    def create_demo_data(self, user_id: str):
        if user_id in CRYPTO_WALLETS_DB:
            return

        CRYPTO_WALLETS_DB[user_id] = {
            "user_id": user_id,
            "balances": {
                "BTC": 0.85,
                "ETH": 12.5,
                "SOL": 150.0,
                "USDT": 25000.0,
                "USDC": 10000.0,
                "ADA": 5000.0,
                "DOT": 200.0,
                "AVAX": 75.0,
                "LINK": 300.0,
                "MATIC": 1000.0,
            },
            "staking_positions": [
                {
                    "protocol": "Ethereum 2.0",
                    "currency": "ETH",
                    "amount": 8.0,
                    "apr": 4.5,
                    "rewards_earned": 0.35,
                    "status": "active",
                    "started_at": "2024-01-15T00:00:00Z",
                },
                {
                    "protocol": "Solana",
                    "currency": "SOL",
                    "amount": 100.0,
                    "apr": 6.8,
                    "rewards_earned": 5.2,
                    "status": "active",
                    "started_at": "2024-02-01T00:00:00Z",
                },
                {
                    "protocol": "Cardano",
                    "currency": "ADA",
                    "amount": 3000.0,
                    "apr": 3.2,
                    "rewards_earned": 85.0,
                    "status": "active",
                    "started_at": "2024-03-10T00:00:00Z",
                },
            ],
            "defi_positions": [
                {
                    "protocol": "Aave",
                    "type": "lending",
                    "deposited_currency": "USDC",
                    "deposited_amount": 10000.0,
                    "deposited_value_usd": 10000.0,
                    "apy": 3.5,
                    "yield_earned_usd": 145.50,
                    "status": "active",
                },
                {
                    "protocol": "Uniswap",
                    "type": "liquidity_pool",
                    "pool": "ETH/USDC",
                    "deposited_value_usd": 5000.0,
                    "apy": 12.0,
                    "yield_earned_usd": 280.00,
                    "status": "active",
                },
                {
                    "protocol": "Lido",
                    "type": "liquid_staking",
                    "deposited_currency": "ETH",
                    "deposited_amount": 4.5,
                    "deposited_value_usd": 15525.0,
                    "apy": 4.2,
                    "yield_earned_usd": 325.80,
                    "status": "active",
                },
            ],
            "transactions": [
                {"id": str(uuid.uuid4()), "type": "buy", "currency": "BTC", "amount": 0.1, "value_usd": 6750.0, "timestamp": "2024-12-01T10:30:00Z", "status": "completed"},
                {"id": str(uuid.uuid4()), "type": "sell", "currency": "ETH", "amount": 2.0, "value_usd": 6900.0, "timestamp": "2024-12-02T14:15:00Z", "status": "completed"},
                {"id": str(uuid.uuid4()), "type": "stake", "currency": "SOL", "amount": 50.0, "value_usd": 7250.0, "timestamp": "2024-12-03T09:00:00Z", "status": "completed"},
                {"id": str(uuid.uuid4()), "type": "transfer", "currency": "USDT", "amount": 5000.0, "value_usd": 5000.0, "timestamp": "2024-12-04T16:45:00Z", "status": "completed"},
                {"id": str(uuid.uuid4()), "type": "defi_deposit", "currency": "USDC", "amount": 10000.0, "value_usd": 10000.0, "timestamp": "2024-12-05T11:00:00Z", "status": "completed"},
                {"id": str(uuid.uuid4()), "type": "swap", "currency": "ETH", "amount": 1.5, "value_usd": 5175.0, "timestamp": "2024-12-06T08:30:00Z", "status": "completed"},
                {"id": str(uuid.uuid4()), "type": "reward", "currency": "ETH", "amount": 0.15, "value_usd": 517.50, "timestamp": "2024-12-07T00:00:00Z", "status": "completed"},
            ],
        }
