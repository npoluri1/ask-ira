from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

STAKING_RATES: Dict[str, float] = {
    "ETH": 4.5,
    "SOL": 7.2,
    "ADA": 3.8,
    "DOT": 14.5,
    "MATIC": 5.2,
    "BNB": 3.5,
}

UNBONDING_PERIODS: Dict[str, int] = {
    "ETH": 5,
    "SOL": 3,
    "ADA": 5,
    "DOT": 28,
    "MATIC": 7,
    "BNB": 7,
}

VALIDATORS: Dict[str, List[Dict[str, Any]]] = {
    "ETH": [
        {"name": "Lido", "commission": 10.0, "status": "active", "staked": 8900000, "apy": 4.7},
        {"name": "RocketPool", "commission": 15.0, "status": "active", "staked": 1200000, "apy": 4.5},
        {"name": "Coinbase", "commission": 25.0, "status": "active", "staked": 2100000, "apy": 4.2},
    ],
    "SOL": [
        {"name": "Jito", "commission": 5.0, "status": "active", "staked": 12000000, "apy": 7.5},
        {"name": "Marinade", "commission": 7.5, "status": "active", "staked": 8500000, "apy": 7.2},
    ],
    "ADA": [
        {"name": "Binance", "commission": 5.0, "status": "active", "staked": 500000000, "apy": 3.8},
        {"name": "Daedalus", "commission": 3.0, "status": "active", "staked": 350000000, "apy": 4.0},
    ],
    "DOT": [
        {"name": "Kraken", "commission": 12.0, "status": "active", "staked": 45000000, "apy": 14.5},
        {"name": "Figment", "commission": 10.0, "status": "active", "staked": 32000000, "apy": 14.8},
    ],
    "MATIC": [
        {"name": "Stader", "commission": 8.0, "status": "active", "staked": 15000000, "apy": 5.2},
    ],
    "BNB": [
        {"name": "PancakeSwap", "commission": 5.0, "status": "active", "staked": 8000000, "apy": 3.5},
        {"name": "TrustWallet", "commission": 3.0, "status": "active", "staked": 12000000, "apy": 3.7},
    ],
}


class StakingPosition:
    def __init__(
        self,
        stake_id: str,
        user_id: str,
        wallet_id: str,
        currency: str,
        amount: float,
        rewards: float,
        validator: str,
        apy: float,
        status: str,
        started_at: float,
        unbonding_at: Optional[float],
    ) -> None:
        self.stake_id = stake_id
        self.user_id = user_id
        self.wallet_id = wallet_id
        self.currency = currency
        self.amount = amount
        self.rewards = rewards
        self.validator = validator
        self.apy = apy
        self.status = status
        self.started_at = started_at
        self.unbonding_at = unbonding_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stake_id": self.stake_id,
            "user_id": self.user_id,
            "wallet_id": self.wallet_id,
            "currency": self.currency,
            "amount": self.amount,
            "rewards": self.rewards,
            "validator": self.validator,
            "apy": self.apy,
            "status": self.status,
            "started_at": self.started_at,
            "unbonding_at": self.unbonding_at,
        }


class StakingEngine:
    def __init__(self) -> None:
        self.STAKING_DB: Dict[str, Dict[str, StakingPosition]] = {}

    def stake(
        self,
        user_id: str,
        wallet_id: str,
        amount: float,
        currency: str,
        validator: str,
    ) -> StakingPosition:
        from .wallets import CryptoWalletEngine

        currency_upper = currency.upper()
        if currency_upper not in STAKING_RATES:
            raise ValueError(f"Staking not available for {currency}")
        validators = VALIDATORS.get(currency_upper, [])
        if not any(v["name"] == validator for v in validators):
            raise ValueError(f"Validator {validator} not found for {currency}")

        wallets_engine = CryptoWalletEngine()
        wallet = wallets_engine.get_wallet(user_id, wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found")
        if wallet.balance < amount:
            raise ValueError(f"Insufficient balance: {wallet.balance} < {amount}")
        if wallet.currency != currency_upper:
            raise ValueError(f"Wallet currency {wallet.currency} doesn't match {currency_upper}")

        wallet.balance -= amount
        stake_id = str(uuid.uuid4())
        apy = STAKING_RATES[currency_upper]

        position = StakingPosition(
            stake_id=stake_id,
            user_id=user_id,
            wallet_id=wallet_id,
            currency=currency_upper,
            amount=amount,
            rewards=0.0,
            validator=validator,
            apy=apy,
            status="active",
            started_at=time.time(),
            unbonding_at=None,
        )
        if user_id not in self.STAKING_DB:
            self.STAKING_DB[user_id] = {}
        self.STAKING_DB[user_id][stake_id] = position
        return position

    def unstake(self, user_id: str, stake_id: str) -> Dict[str, Any]:
        user_positions = self.STAKING_DB.get(user_id, {})
        position = user_positions.get(stake_id)
        if position is None:
            raise ValueError(f"Stake {stake_id} not found")
        if position.status != "active":
            raise ValueError(f"Stake {stake_id} is not active")

        unbonding_days = UNBONDING_PERIODS.get(position.currency, 7)
        unbonding_at = time.time() + unbonding_days * 86400
        position.status = "unbonding"
        position.unbonding_at = unbonding_at

        return {
            "stake_id": stake_id,
            "currency": position.currency,
            "amount": position.amount,
            "rewards": position.rewards,
            "status": "unbonding",
            "unbonding_days": unbonding_days,
            "unbonding_until": unbonding_at,
        }

    def get_staking_positions(self, user_id: str) -> List[StakingPosition]:
        user_positions = self.STAKING_DB.get(user_id, {})
        return list(user_positions.values())

    def get_rewards(self, user_id: str, stake_id: str) -> Dict[str, Any]:
        user_positions = self.STAKING_DB.get(user_id, {})
        position = user_positions.get(stake_id)
        if position is None:
            raise ValueError(f"Stake {stake_id} not found")
        if position.status == "active":
            elapsed = time.time() - position.started_at
            days = elapsed / 86400
            accrued = position.amount * (position.apy / 100) * (days / 365)
            position.rewards = round(accrued, 8)
        return {
            "stake_id": stake_id,
            "currency": position.currency,
            "staked_amount": position.amount,
            "accumulated_rewards": position.rewards,
            "apy": position.apy,
        }

    def claim_rewards(self, user_id: str, stake_id: str) -> Dict[str, Any]:
        user_positions = self.STAKING_DB.get(user_id, {})
        position = user_positions.get(stake_id)
        if position is None:
            raise ValueError(f"Stake {stake_id} not found")
        if position.status != "active":
            raise ValueError("Can only claim rewards on active stakes")

        self.get_rewards(user_id, stake_id)
        claimed = position.rewards
        position.amount += claimed
        position.rewards = 0.0

        return {
            "stake_id": stake_id,
            "currency": position.currency,
            "rewards_claimed": claimed,
            "new_staked_amount": position.amount,
            "compounded": True,
        }

    def get_staking_rates(self) -> Dict[str, Any]:
        return {
            currency: {
                "apy_percent": rate,
                "unbonding_days": UNBONDING_PERIODS.get(currency, 7),
                "validators": len(VALIDATORS.get(currency, [])),
            }
            for currency, rate in STAKING_RATES.items()
        }

    def calculate_projected_rewards(
        self,
        amount: float,
        currency: str,
        duration_days: int,
    ) -> Dict[str, Any]:
        currency_upper = currency.upper()
        if currency_upper not in STAKING_RATES:
            raise ValueError(f"Staking not available for {currency}")
        apy = STAKING_RATES[currency_upper]
        years = duration_days / 365
        gross_reward = amount * (apy / 100) * years
        compound_reward = amount * ((1 + (apy / 100) / 365) ** duration_days - 1)
        return {
            "currency": currency_upper,
            "amount": amount,
            "duration_days": duration_days,
            "apy": apy,
            "estimated_gross_reward": round(gross_reward, 8),
            "estimated_compound_reward": round(compound_reward, 8),
            "estimated_total": round(amount + compound_reward, 8),
        }

    def get_validators(self, currency: str) -> List[Dict[str, Any]]:
        currency_upper = currency.upper()
        if currency_upper not in VALIDATORS:
            raise ValueError(f"No validators found for {currency}")
        return VALIDATORS[currency_upper]

    def create_demo_data(self, user_id: str) -> List[StakingPosition]:
        demo_stakes = [
            ("ETH", 10.0, "Lido", 4.5),
            ("SOL", 100.0, "Jito", 7.2),
            ("DOT", 500.0, "Kraken", 14.5),
        ]
        created: List[StakingPosition] = []
        now = time.time()
        for currency, amount, validator, apy in demo_stakes:
            stake_id = str(uuid.uuid4())
            position = StakingPosition(
                stake_id=stake_id,
                user_id=user_id,
                wallet_id="",
                currency=currency,
                amount=amount,
                rewards=amount * (apy / 100) * 0.5,
                validator=validator,
                apy=apy,
                status="active",
                started_at=now - 180 * 86400,
                unbonding_at=None,
            )
            if user_id not in self.STAKING_DB:
                self.STAKING_DB[user_id] = {}
            self.STAKING_DB[user_id][stake_id] = position
            created.append(position)
        return created
