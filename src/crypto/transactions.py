from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

SUPPORTED_NETWORKS = {
    "bitcoin",
    "ethereum",
    "erc20",
    "solana",
    "binance_smart_chain",
    "polygon",
}

FEE_LEVELS = {"slow", "standard", "fast"}

NETWORK_FEE_ESTIMATES: Dict[str, Dict[str, Dict[str, int]]] = {
    "bitcoin": {
        "slow": {"sat_per_vbyte": 20, "estimated_minutes": 60},
        "standard": {"sat_per_vbyte": 50, "estimated_minutes": 20},
        "fast": {"sat_per_vbyte": 120, "estimated_minutes": 5},
    },
    "ethereum": {
        "slow": {"gwei": 15, "estimated_minutes": 10},
        "standard": {"gwei": 30, "estimated_minutes": 3},
        "fast": {"gwei": 80, "estimated_minutes": 1},
    },
    "erc20": {
        "slow": {"gwei": 20, "estimated_minutes": 10},
        "standard": {"gwei": 40, "estimated_minutes": 3},
        "fast": {"gwei": 100, "estimated_minutes": 1},
    },
    "solana": {
        "slow": {"lamports": 5000, "estimated_minutes": 1},
        "standard": {"lamports": 10000, "estimated_minutes": 0.5},
        "fast": {"lamports": 25000, "estimated_minutes": 0.2},
    },
    "polygon": {
        "slow": {"gwei": 30, "estimated_minutes": 10},
        "standard": {"gwei": 60, "estimated_minutes": 3},
        "fast": {"gwei": 150, "estimated_minutes": 1},
    },
}

NETWORK_STATUS: Dict[str, Dict[str, Any]] = {
    "bitcoin": {"block_height": 842000, "tps": 7, "mempool_size_mb": 45, "congestion": "low"},
    "ethereum": {"block_height": 19750000, "tps": 15, "base_fee_gwei": 25, "congestion": "moderate"},
    "solana": {"block_height": 265000000, "tps": 2800, "congestion": "low"},
    "polygon": {"block_height": 52500000, "tps": 35, "congestion": "low"},
}

ADDRESS_PATTERNS: Dict[str, str] = {
    "BTC": r"^[13][a-km-zA-HJ-NP-Z0-9]{26,33}$",
    "ETH": r"^0x[a-fA-F0-9]{40}$",
    "USDT": r"^0x[a-fA-F0-9]{40}$",
    "USDC": r"^0x[a-fA-F0-9]{40}$",
    "SOL": r"^[1-9A-HJ-NP-Za-km-z]{32,44}$",
    "XRP": r"^r[1-9A-HJ-NP-Za-km-z]{25,34}$",
    "ADA": r"^addr1[a-z0-9]{58}$",
    "DOT": r"^1[1-9A-HJ-NP-Za-km-z]{47}$",
    "MATIC": r"^0x[a-fA-F0-9]{40}$",
    "BNB": r"^bnb1[a-z0-9]{38}$",
}


def _generate_tx_hash() -> str:
    return "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:32]


class Transaction:
    def __init__(
        self,
        tx_id: str,
        user_id: str,
        wallet_id: str,
        tx_type: str,
        from_address: str,
        to_address: str,
        amount: float,
        currency: str,
        network: str,
        fee: float,
        fee_unit: str,
        status: str,
        confirmations: int,
        block_number: int,
        tx_hash: str,
        timestamp: float,
    ) -> None:
        self.tx_id = tx_id
        self.user_id = user_id
        self.wallet_id = wallet_id
        self.type = tx_type
        self.from_address = from_address
        self.to_address = to_address
        self.amount = amount
        self.currency = currency
        self.network = network
        self.fee = fee
        self.fee_unit = fee_unit
        self.status = status
        self.confirmations = confirmations
        self.block_number = block_number
        self.tx_hash = tx_hash
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "user_id": self.user_id,
            "wallet_id": self.wallet_id,
            "type": self.type,
            "from": self.from_address,
            "to": self.to_address,
            "amount": self.amount,
            "currency": self.currency,
            "network": self.network,
            "fee": self.fee,
            "fee_unit": self.fee_unit,
            "status": self.status,
            "confirmations": self.confirmations,
            "block_number": self.block_number,
            "tx_hash": self.tx_hash,
            "timestamp": self.timestamp,
        }


class SwapOrder:
    def __init__(
        self,
        swap_id: str,
        user_id: str,
        from_currency: str,
        to_currency: str,
        from_amount: float,
        to_amount: float,
        exchange_rate: float,
        fee: float,
        slippage: float,
        timestamp: float,
        status: str,
    ) -> None:
        self.swap_id = swap_id
        self.user_id = user_id
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.from_amount = from_amount
        self.to_amount = to_amount
        self.exchange_rate = exchange_rate
        self.fee = fee
        self.slippage = slippage
        self.timestamp = timestamp
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "swap_id": self.swap_id,
            "user_id": self.user_id,
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "from_amount": self.from_amount,
            "to_amount": self.to_amount,
            "exchange_rate": self.exchange_rate,
            "fee": self.fee,
            "slippage": self.slippage,
            "timestamp": self.timestamp,
            "status": self.status,
        }


class CryptoTransactionsEngine:
    def __init__(self) -> None:
        self.TX_DB: Dict[str, Transaction] = {}
        self.SWAP_DB: Dict[str, SwapOrder] = {}

    def send_crypto(
        self,
        user_id: str,
        wallet_id: str,
        to_address: str,
        amount: float,
        currency: str,
        network: str,
        fee_level: str = "standard",
    ) -> Transaction:
        from .wallets import CryptoWalletEngine

        wallets_engine = CryptoWalletEngine()
        wallet = wallets_engine.get_wallet(user_id, wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found")
        if wallet.balance < amount:
            raise ValueError(
                f"Insufficient balance: {wallet.balance} {currency} < {amount} {currency}"
            )
        if network not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported network: {network}")
        if fee_level not in FEE_LEVELS:
            raise ValueError(f"Invalid fee level: {fee_level}. Use slow, standard, or fast")

        fee_info = self.estimate_fee(network, fee_level)
        tx_id = str(uuid.uuid4())
        tx_hash = _generate_tx_hash()
        now = time.time()

        wallet.balance -= amount

        tx = Transaction(
            tx_id=tx_id,
            user_id=user_id,
            wallet_id=wallet_id,
            tx_type="send",
            from_address=wallet.address,
            to_address=to_address,
            amount=amount,
            currency=currency.upper(),
            network=network,
            fee=fee_info["estimated_fee_native"],
            fee_unit=fee_info["unit"],
            status="confirmed",
            confirmations=0,
            block_number=0,
            tx_hash=tx_hash,
            timestamp=now,
        )
        self.TX_DB[tx_id] = tx
        return tx

    def receive_crypto(
        self,
        user_id: str,
        wallet_id: str,
        from_address: str,
        amount: float,
        currency: str,
        network: str,
    ) -> Transaction:
        from .wallets import CryptoWalletEngine

        wallets_engine = CryptoWalletEngine()
        wallet = wallets_engine.get_wallet(user_id, wallet_id)
        if wallet is None:
            raise ValueError(f"Wallet {wallet_id} not found")
        if network not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported network: {network}")

        tx_id = str(uuid.uuid4())
        tx_hash = _generate_tx_hash()
        now = time.time()

        wallet.balance += amount

        tx = Transaction(
            tx_id=tx_id,
            user_id=user_id,
            wallet_id=wallet_id,
            tx_type="receive",
            from_address=from_address,
            to_address=wallet.address,
            amount=amount,
            currency=currency.upper(),
            network=network,
            fee=0.0,
            fee_unit="",
            status="confirmed",
            confirmations=12,
            block_number=0,
            tx_hash=tx_hash,
            timestamp=now,
        )
        self.TX_DB[tx_id] = tx
        return tx

    def swap_crypto(
        self,
        user_id: str,
        from_wallet_id: str,
        to_wallet_id: str,
        from_currency: str,
        to_currency: str,
        amount: float,
        slippage: float = 0.5,
    ) -> SwapOrder:
        from .wallets import CryptoWalletEngine

        wallets_engine = CryptoWalletEngine()
        from_wallet = wallets_engine.get_wallet(user_id, from_wallet_id)
        to_wallet = wallets_engine.get_wallet(user_id, to_wallet_id)
        if from_wallet is None or to_wallet is None:
            raise ValueError("Source or destination wallet not found")
        if from_wallet.balance < amount:
            raise ValueError("Insufficient balance for swap")

        mock_rates: Dict[str, float] = {
            "BTC": 67450.0,
            "ETH": 3450.0,
            "USDT": 1.0,
            "USDC": 1.0,
            "SOL": 142.0,
            "XRP": 0.62,
            "ADA": 0.45,
            "DOT": 7.80,
            "MATIC": 0.72,
            "BNB": 580.0,
        }
        from_rate = mock_rates.get(from_currency.upper(), 1.0)
        to_rate = mock_rates.get(to_currency.upper(), 1.0)
        exchange_rate = from_rate / to_rate if to_rate != 0 else 0
        to_amount = amount * exchange_rate * (1 - slippage / 100)
        swap_fee = amount * 0.003

        from_wallet.balance -= amount
        to_wallet.balance += to_amount

        swap_id = str(uuid.uuid4())
        swap = SwapOrder(
            swap_id=swap_id,
            user_id=user_id,
            from_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            from_amount=amount,
            to_amount=round(to_amount, 8),
            exchange_rate=round(exchange_rate, 8),
            fee=round(swap_fee, 8),
            slippage=slippage,
            timestamp=time.time(),
            status="completed",
        )
        self.SWAP_DB[swap_id] = swap
        return swap

    def get_transactions(
        self,
        user_id: str,
        wallet_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        filtered: List[Transaction] = []
        for tx in self.TX_DB.values():
            if tx.user_id != user_id:
                continue
            if wallet_id is not None and tx.wallet_id != wallet_id:
                continue
            filtered.append(tx)
        filtered.sort(key=lambda t: t.timestamp, reverse=True)
        page = filtered[offset:offset + limit]
        return {
            "transactions": [t.to_dict() for t in page],
            "total": len(filtered),
            "limit": limit,
            "offset": offset,
        }

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        return self.TX_DB.get(tx_id)

    def estimate_fee(self, network: str, fee_level: str = "standard") -> Dict[str, Any]:
        if network not in NETWORK_FEE_ESTIMATES:
            raise ValueError(f"Unsupported network: {network}")
        if fee_level not in FEE_LEVELS:
            raise ValueError(f"Invalid fee level: {fee_level}")
        net_data = NETWORK_FEE_ESTIMATES[network]
        level_data = net_data[fee_level]
        if network == "bitcoin":
            fee_sats = level_data["sat_per_vbyte"] * 250
            return {
                "network": network,
                "fee_level": fee_level,
                "sat_per_vbyte": level_data["sat_per_vbyte"],
                "estimated_fee_sats": fee_sats,
                "estimated_fee_native": round(fee_sats / 1e8, 8),
                "estimated_minutes": level_data["estimated_minutes"],
                "unit": "BTC",
            }
        if network in ("ethereum", "erc20", "polygon"):
            fee_gwei = level_data["gwei"] * 21000
            return {
                "network": network,
                "fee_level": fee_level,
                "gwei": level_data["gwei"],
                "estimated_fee_gwei": fee_gwei,
                "estimated_fee_eth": round(fee_gwei / 1e9, 8),
                "estimated_minutes": level_data["estimated_minutes"],
                "unit": "ETH" if network != "polygon" else "MATIC",
            }
        if network == "solana":
            return {
                "network": network,
                "fee_level": fee_level,
                "lamports": level_data["lamports"],
                "estimated_fee_sol": round(level_data["lamports"] / 1e9, 10),
                "estimated_minutes": level_data["estimated_minutes"],
                "unit": "SOL",
            }
        raise ValueError(f"Cannot compute fee for network: {network}")

    def validate_address(self, address: str, currency: str) -> Dict[str, Any]:
        currency_upper = currency.upper()
        if currency_upper not in ADDRESS_PATTERNS:
            return {"valid": False, "currency": currency_upper, "reason": "Unsupported currency"}
        prefix_match = (
            (currency_upper == "BTC" and address.startswith(("1", "3", "bc1")))
            or (currency_upper in ("ETH", "USDT", "USDC", "MATIC") and address.startswith("0x"))
            or (currency_upper == "SOL" and len(address) >= 32)
            or (currency_upper == "XRP" and address.startswith("r"))
            or (currency_upper == "ADA" and address.startswith("addr1"))
            or (currency_upper == "DOT" and address.startswith("1"))
            or (currency_upper == "BNB" and address.startswith("bnb1"))
        )
        if not prefix_match:
            return {
                "valid": False,
                "currency": currency_upper,
                "reason": f"Invalid prefix for {currency_upper}",
            }
        length_ok = len(address) >= 26 and len(address) <= 60
        return {
            "valid": prefix_match and length_ok,
            "currency": currency_upper,
            "length": len(address),
        }

    def get_network_status(self, network: str) -> Dict[str, Any]:
        if network not in NETWORK_STATUS:
            raise ValueError(f"Unsupported network: {network}")
        base = NETWORK_STATUS[network]
        return {"network": network, **base}

    def create_demo_data(self, user_id: str, wallet_ids: List[str]) -> List[Transaction]:
        if not wallet_ids:
            return []
        txs: List[Transaction] = []
        now = time.time()
        for i, wid in enumerate(wallet_ids[:3]):
            tx = Transaction(
                tx_id=str(uuid.uuid4()),
                user_id=user_id,
                wallet_id=wid,
                tx_type="receive",
                from_address=_generate_tx_hash()[:42],
                to_address=_generate_tx_hash()[:42],
                amount=1.0 + i,
                currency="ETH",
                network="ethereum",
                fee=0.003,
                fee_unit="ETH",
                status="confirmed",
                confirmations=24,
                block_number=19750000 - i * 100,
                tx_hash=_generate_tx_hash(),
                timestamp=now - i * 86400,
            )
            self.TX_DB[tx.tx_id] = tx
            txs.append(tx)
        return txs
