from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

SUPPORTED_CURRENCIES = {"BTC", "ETH", "USDT", "USDC", "SOL", "XRP", "ADA", "DOT", "MATIC", "BNB"}

CURRENCY_PREFIXES = {
    "BTC": "1",
    "ETH": "0x",
    "USDT": "0x",
    "USDC": "0x",
    "SOL": "8",
    "XRP": "r",
    "ADA": "addr1",
    "DOT": "1",
    "MATIC": "0x",
    "BNB": "bnb1",
}

CURRENCY_DERIVATION_COINS = {
    "BTC": "0'",
    "ETH": "60'",
    "USDT": "60'",
    "USDC": "60'",
    "SOL": "501'",
    "XRP": "144'",
    "ADA": "1815'",
    "DOT": "354'",
    "MATIC": "966'",
    "BNB": "714'",
}

MOCK_USD_RATES: Dict[str, float] = {
    "BTC": 67450.00,
    "ETH": 3450.00,
    "USDT": 1.00,
    "USDC": 1.00,
    "SOL": 142.00,
    "XRP": 0.62,
    "ADA": 0.45,
    "DOT": 7.80,
    "MATIC": 0.72,
    "BNB": 580.00,
}


def _generate_mock_address(currency: str) -> str:
    prefix = CURRENCY_PREFIXES.get(currency, "0x")
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    if prefix == "1":
        return prefix + raw[:33]
    if prefix == "r":
        return prefix + raw[:34]
    if prefix in ("addr1", "bnb1"):
        return prefix + raw[:51]
    return prefix + raw[:40]


def _generate_xpub(currency: str) -> str:
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    coin = CURRENCY_DERIVATION_COINS.get(currency, "0'")
    return f"xpub6{raw[:100]}_{coin}"


def _generate_private_key_wif(currency: str) -> str:
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    return f"L{raw[:50]}"


def _generate_demo_balance(currency: str) -> float:
    return {
        "BTC": 0.5,
        "ETH": 12.0,
        "USDT": 10000.0,
        "USDC": 5000.0,
        "SOL": 250.0,
        "XRP": 15000.0,
        "ADA": 50000.0,
        "DOT": 2000.0,
        "MATIC": 10000.0,
        "BNB": 50.0,
    }.get(currency, 0.0)


class Wallet:
    def __init__(
        self,
        wallet_id: str,
        user_id: str,
        currency: str,
        name: str,
        address: str,
        balance: float,
        wallet_type: str,
        created_at: float,
        xpub: str,
        derivation_path: str,
    ) -> None:
        self.wallet_id = wallet_id
        self.user_id = user_id
        self.currency = currency
        self.name = name
        self.address = address
        self.balance = balance
        self.type = wallet_type
        self.created_at = created_at
        self.xpub = xpub
        self.derivation_path = derivation_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "user_id": self.user_id,
            "currency": self.currency,
            "name": self.name,
            "address": self.address,
            "balance": self.balance,
            "usd_value": self.balance * MOCK_USD_RATES.get(self.currency, 0.0),
            "type": self.type,
            "created_at": self.created_at,
            "xpub": self.xpub,
            "derivation_path": self.derivation_path,
        }


class MultiSigWallet:
    def __init__(
        self,
        wallet_id: str,
        user_id: str,
        currency: str,
        address: str,
        signers: List[str],
        required_signatures: int,
        balance: float,
        created_at: float,
    ) -> None:
        self.wallet_id = wallet_id
        self.user_id = user_id
        self.currency = currency
        self.address = address
        self.signers = signers
        self.required_signatures = required_signatures
        self.balance = balance
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "user_id": self.user_id,
            "currency": self.currency,
            "address": self.address,
            "signers": self.signers,
            "required_signatures": self.required_signatures,
            "balance": self.balance,
            "usd_value": self.balance * MOCK_USD_RATES.get(self.currency, 0.0),
            "type": "multi_sig",
            "created_at": self.created_at,
        }


class CryptoWalletEngine:
    WALLETS_DB: Dict[str, Dict[str, Any]] = {}
    MULTI_SIG_DB: Dict[str, Dict[str, Any]] = {}
    _address_index: Dict[str, int] = {}

    def __init__(self) -> None:
        pass

    def create_wallet(
        self,
        user_id: str,
        currency: str,
        name: str,
        wallet_type: str = "hot",
    ) -> Wallet:
        if currency.upper() not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}. Supported: {SUPPORTED_CURRENCIES}")
        if wallet_type not in ("hot", "cold"):
            raise ValueError("wallet_type must be 'hot' or 'cold'")
        wallet_id = str(uuid.uuid4())
        address = _generate_mock_address(currency.upper())
        now = time.time()
        coin_code = CURRENCY_DERIVATION_COINS.get(currency.upper(), "0'")
        xpub = _generate_xpub(currency.upper())
        derivation_path = f"m/44'/{coin_code}/0'/0/0"
        wallet = Wallet(
            wallet_id=wallet_id,
            user_id=user_id,
            currency=currency.upper(),
            name=name,
            address=address,
            balance=0.0,
            wallet_type=wallet_type,
            created_at=now,
            xpub=xpub,
            derivation_path=derivation_path,
        )
        if user_id not in self.WALLETS_DB:
            self.WALLETS_DB[user_id] = {}
        self.WALLETS_DB[user_id][wallet_id] = wallet
        return wallet

    def get_wallets(self, user_id: str) -> List[Wallet]:
        user_wallets = self.WALLETS_DB.get(user_id, {})
        multi_sig_user = self.MULTI_SIG_DB.get(user_id, {})
        result = list(user_wallets.values())
        result.extend(multi_sig_user.values())
        return result

    def get_wallet(self, user_id: str, wallet_id: str) -> Optional[Any]:
        user_wallets = self.WALLETS_DB.get(user_id, {})
        if wallet_id in user_wallets:
            return user_wallets[wallet_id]
        multi_sig_user = self.MULTI_SIG_DB.get(user_id, {})
        return multi_sig_user.get(wallet_id)

    def get_balance(self, user_id: str, wallet_id: str) -> Dict[str, float]:
        wallet = self.get_wallet(user_id, wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found for user {user_id}")
        rate = MOCK_USD_RATES.get(wallet.currency, 0.0)
        return {
            "balance": wallet.balance,
            "usd_value": wallet.balance * rate,
        }

    def get_total_portfolio(self, user_id: str) -> Dict[str, Any]:
        wallets = self.get_wallets(user_id)
        total_usd = 0.0
        breakdown: Dict[str, float] = {}
        for w in wallets:
            rate = MOCK_USD_RATES.get(w.currency, 0.0)
            usd = w.balance * rate
            total_usd += usd
            if w.currency not in breakdown:
                breakdown[w.currency] = 0.0
            breakdown[w.currency] += usd
        return {
            "user_id": user_id,
            "total_usd": round(total_usd, 2),
            "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
            "wallet_count": len(wallets),
        }

    def create_multi_sig_wallet(
        self,
        user_id: str,
        currency: str,
        signers: List[str],
        required_signatures: int,
    ) -> MultiSigWallet:
        if currency.upper() not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        n = len(signers)
        if required_signatures not in (2, 3) or (required_signatures != 2 and required_signatures != 3):
            raise ValueError("required_signatures must be 2 or 3")
        if required_signatures > n:
            raise ValueError(f"Cannot require {required_signatures} sigs from {n} signers")
        if n not in (3, 5):
            raise ValueError("Multi-sig wallets must have 3 or 5 signers")
        wallet_id = str(uuid.uuid4())
        address = _generate_mock_address(currency.upper())
        now = time.time()
        wallet = MultiSigWallet(
            wallet_id=wallet_id,
            user_id=user_id,
            currency=currency.upper(),
            address=address,
            signers=signers,
            required_signatures=required_signatures,
            balance=0.0,
            created_at=now,
        )
        if user_id not in self.MULTI_SIG_DB:
            self.MULTI_SIG_DB[user_id] = {}
        self.MULTI_SIG_DB[user_id][wallet_id] = wallet
        return wallet

    def generate_deposit_address(self, user_id: str, wallet_id: str) -> Dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found")
        if user_id not in self._address_index:
            self._address_index[user_id] = 0
        self._address_index[user_id] += 1
        index = self._address_index[user_id]
        new_address = _generate_mock_address(wallet.currency)
        coin_code = CURRENCY_DERIVATION_COINS.get(wallet.currency, "0'")
        child_path = f"m/44'/{coin_code}/0'/0/{index}"
        return {
            "address": new_address,
            "derivation_path": child_path,
            "index": index,
            "currency": wallet.currency,
        }

    def export_private_key(self, user_id: str, wallet_id: str) -> Dict[str, str]:
        wallet = self.get_wallet(user_id, wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found")
        wif = _generate_private_key_wif(wallet.currency)
        return {
            "wallet_id": wallet_id,
            "currency": wallet.currency,
            "private_key_wif": wif,
            "encrypted": True,
            "format": "WIF",
        }

    def create_demo_data(self, user_id: str) -> List[Wallet]:
        demo_wallets = [
            ("BTC", "Bitcoin Savings", "cold", 0.5),
            ("ETH", "Ethereum Main", "hot", 12.0),
            ("USDT", "USDT Wallet", "hot", 10000.0),
            ("SOL", "Solana Staking", "hot", 250.0),
            ("ADA", "Cardano Holdings", "cold", 50000.0),
        ]
        created: List[Wallet] = []
        for currency, name, wtype, balance in demo_wallets:
            wallet = self.create_wallet(user_id, currency, name, wtype)
            wallet.balance = balance
            self.WALLETS_DB[user_id][wallet.wallet_id] = wallet
            created.append(wallet)
        return created
