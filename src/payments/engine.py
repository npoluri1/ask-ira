import copy
import time
import uuid
from typing import Any, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_PAYMENT_TYPES: list[str] = [
    "wire", "swift", "sepa_credit", "sepa_direct_debit",
    "ach_credit", "ach_debit", "faster_payments", "internal",
    "crypto", "rtp", "pix", "upi",
]

SUPPORTED_CURRENCIES: list[str] = [
    "USD", "EUR", "GBP", "JPY", "AED", "SAR", "INR", "SGD",
    "CHF", "CAD", "AUD", "CNY", "HKD", "KRW", "BRL",
]

PAYMENT_STATUS_STAGES: dict[str, list[str]] = {
    "pending": ["pending"],
    "processing": ["pending", "processing"],
    "completed": ["pending", "processing", "completed"],
    "failed": ["pending", "failed"],
    "cancelled": ["cancelled"],
}

FEE_SCHEDULE: dict[str, float] = {
    "wire": 30.0,
    "swift": 25.0,
    "sepa_credit": 1.0,
    "sepa_direct_debit": 0.5,
    "ach_credit": 0.5,
    "ach_debit": 0.5,
    "faster_payments": 1.0,
    "internal": 0.0,
    "crypto": 0.0,
    "rtp": 0.1,
    "pix": 0.0,
    "upi": 0.0,
}

CRYPTO_FEE_PERCENT: float = 0.001
FX_FEE_PERCENT: float = 0.005

DELIVERY_ESTIMATES: dict[str, dict[str, str]] = {
    "wire": {"standard": "1-3 business days", "express": "same day"},
    "swift": {"standard": "2-5 business days", "express": "1 business day"},
    "sepa_credit": {"standard": "1 business day", "express": "instant (<10s)"},
    "sepa_direct_debit": {"standard": "1 business day", "express": "N/A"},
    "ach_credit": {"standard": "1-2 business days", "express": "same day"},
    "ach_debit": {"standard": "1-2 business days", "express": "same day"},
    "faster_payments": {"standard": "instant (<2min)", "express": "instant (<2min)"},
    "internal": {"standard": "instant", "express": "instant"},
    "crypto": {"standard": "10-60 minutes", "express": "10-60 minutes"},
    "rtp": {"standard": "instant", "express": "instant"},
    "pix": {"standard": "instant", "express": "instant"},
    "upi": {"standard": "instant", "express": "instant"},
}


def _generate_id() -> str:
    return f"pay_{uuid.uuid4().hex[:24]}"


def _now() -> float:
    return time.time()


def _calculate_crypto_fee(amount: float, currency: str) -> float:
    base = amount * CRYPTO_FEE_PERCENT
    network_fees: dict[str, float] = {
        "BTC": 0.0005, "ETH": 0.002, "USDT": 1.0, "USDC": 1.0,
    }
    return base + network_fees.get(currency.upper(), 0.5)


class PaymentsEngine:
    PYMENT_DB: dict[str, dict[str, Any]] = {}

    def create_payment(
        self,
        user_id: str,
        amount: float,
        currency: str,
        from_currency: str,
        to_currency: str,
        beneficiary: str,
        payment_type: str,
        description: str = "",
    ) -> dict[str, Any]:
        if payment_type not in SUPPORTED_PAYMENT_TYPES:
            raise ValueError(f"Unsupported payment type: {payment_type}")
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        fees = self.get_fees(amount, currency, payment_type)
        payment_id = _generate_id()
        now = _now()

        payment: dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency.upper(),
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "beneficiary": beneficiary,
            "payment_type": payment_type,
            "description": description,
            "fees": fees,
            "total_charged": round(amount + fees["total_fee"], 2),
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }

        tracking: dict[str, Any] = {
            "payment_id": payment_id,
            "stages": [
                {"stage": "initiated", "timestamp": now, "status": "completed"},
                {"stage": "validated", "timestamp": now + 1, "status": "pending"},
                {"stage": "processing", "timestamp": None, "status": "pending"},
                {"stage": "settled", "timestamp": None, "status": "pending"},
            ],
            "current_stage": "initiated",
            "completed_stages": ["initiated"],
        }

        self.PYMENT_DB[payment_id] = {"payment": payment, "tracking": tracking}
        logger.info("Created payment %s for user %s (%.2f %s)", payment_id, user_id, amount, currency)
        return payment

    def get_payments(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        user_payments: list[dict[str, Any]] = []
        for record in self.PYMENT_DB.values():
            if record["payment"]["user_id"] == user_id:
                user_payments.append(copy.deepcopy(record["payment"]))

        user_payments.sort(key=lambda p: p["created_at"], reverse=True)
        return user_payments[offset:offset + limit]

    def get_payment(self, user_id: str, payment_id: str) -> Optional[dict[str, Any]]:
        record = self.PYMENT_DB.get(payment_id)
        if record is None or record["payment"]["user_id"] != user_id:
            return None
        return copy.deepcopy(record["payment"])

    def get_payment_status(self, user_id: str, payment_id: str) -> Optional[dict[str, Any]]:
        record = self.PYMENT_DB.get(payment_id)
        if record is None or record["payment"]["user_id"] != user_id:
            return None
        return copy.deepcopy(record["tracking"])

    def cancel_payment(self, user_id: str, payment_id: str) -> Optional[dict[str, Any]]:
        record = self.PYMENT_DB.get(payment_id)
        if record is None or record["payment"]["user_id"] != user_id:
            return None
        if record["payment"]["status"] not in ("pending", "processing"):
            raise ValueError(f"Cannot cancel payment in status: {record['payment']['status']}")

        record["payment"]["status"] = "cancelled"
        record["payment"]["updated_at"] = _now()
        record["tracking"]["current_stage"] = "cancelled"
        return copy.deepcopy(record["payment"])

    def get_fees(self, amount: float, currency: str, payment_type: str) -> dict[str, Any]:
        base_fee = FEE_SCHEDULE.get(payment_type, 0.0)
        if payment_type == "crypto":
            crypto_fee = _calculate_crypto_fee(amount, currency)
            total_fee = crypto_fee
        else:
            crypto_fee = 0.0
            total_fee = base_fee

        fx_fee = 0.0
        if payment_type not in ("internal",) and currency.upper() != "USD":
            fx_fee = round(amount * FX_FEE_PERCENT, 2)

        total = round(total_fee + fx_fee, 2)
        return {
            "base_fee": base_fee,
            "crypto_fee": crypto_fee,
            "fx_fee": fx_fee,
            "total_fee": total,
            "currency": currency.upper(),
            "breakdown": {
                "processing_fee": round(total_fee, 2),
                "network_fee": 0.0,
                "conversion_fee": fx_fee,
            },
        }

    def get_estimated_delivery(
        self,
        payment_type: str,
        from_currency: str = "",
        to_currency: str = "",
    ) -> dict[str, Any]:
        estimates = DELIVERY_ESTIMATES.get(payment_type, {"standard": "varies", "express": "varies"})
        same_currency = from_currency.upper() == to_currency.upper() if from_currency and to_currency else True
        fx_delay = " (may add 1 day for FX conversion)" if not same_currency else ""

        return {
            "payment_type": payment_type,
            "standard": estimates["standard"] + fx_delay,
            "express": estimates["express"],
            "currency_pair": f"{from_currency}/{to_currency}" if from_currency and to_currency else "N/A",
        }

    def create_demo_data(self, user_id: str) -> list[str]:
        demos: list[dict[str, Any]] = [
            {"amount": 2500.00, "currency": "USD", "from_currency": "USD", "to_currency": "EUR",
             "beneficiary": "Euro Imports GmbH", "payment_type": "swift", "description": "Invoice INV-2024-8912"},
            {"amount": 150.00, "currency": "EUR", "from_currency": "EUR", "to_currency": "EUR",
             "beneficiary": "Berlin Office Rent", "payment_type": "sepa_credit", "description": "Monthly rent March"},
            {"amount": 3250.75, "currency": "USD", "from_currency": "USD", "to_currency": "USD",
             "beneficiary": "CloudServ Infrastructure", "payment_type": "ach_credit", "description": "Cloud hosting Q1"},
            {"amount": 500.00, "currency": "GBP", "from_currency": "GBP", "to_currency": "GBP",
             "beneficiary": "UK Supplier Ltd", "payment_type": "faster_payments", "description": "Supplier payment"},
            {"amount": 10000.00, "currency": "USD", "from_currency": "USD", "to_currency": "USD",
             "beneficiary": "Internal Account", "payment_type": "internal", "description": "Transfer to ops account"},
            {"amount": 4500.00, "currency": "USD", "from_currency": "USD", "to_currency": "USD",
             "beneficiary": "Crypto Exchange Wallet", "payment_type": "crypto",
             "description": "Crypto investment"},
            {"amount": 45.00, "currency": "USD", "from_currency": "USD", "to_currency": "USD",
             "beneficiary": "Coffee Shop POS", "payment_type": "rtp", "description": "Payment via RTP"},
        ]

        ids: list[str] = []
        for demo in demos:
            payment = self.create_payment(user_id=user_id, **demo)
            ids.append(payment["payment_id"])
            record = self.PYMENT_DB[payment["payment_id"]]
            record["payment"]["status"] = "completed"
            record["tracking"]["current_stage"] = "settled"

        logger.info("Created %d demo payments for user %s", len(demos), user_id)
        return ids
