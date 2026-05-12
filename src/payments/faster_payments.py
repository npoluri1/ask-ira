import uuid
import time
import copy
import re
from typing import Any, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)

FP_FEE: float = 1.0
FP_MAX_SINGLE: float = 1_000_000.0
FP_MAX_DAILY: float = 10_000_000.0


def _generate_id() -> str:
    return f"fp_{uuid.uuid4().hex[:20]}"


def _now() -> float:
    return time.time()


class FasterPaymentsEngine:
    FP_DB: dict[str, dict[str, Any]] = {}

    def create_faster_payment(
        self,
        user_id: str,
        from_account: str,
        to_account: str,
        sort_code: str,
        account_number: str,
        amount: float,
        currency: str = "GBP",
        reference: str = "",
    ) -> dict[str, Any]:
        if currency.upper() != "GBP":
            raise ValueError("Faster Payments requires GBP currency")
        if not self.validate_sort_code(sort_code):
            raise ValueError(f"Invalid sort code: {sort_code}")
        if not self.validate_account_number(account_number):
            raise ValueError(f"Invalid account number: {account_number}")
        if amount > FP_MAX_SINGLE:
            raise ValueError(f"Amount exceeds Faster Payments single limit of £{FP_MAX_SINGLE:,.0f}")

        daily_total = self._get_daily_total(user_id)
        if daily_total + amount > FP_MAX_DAILY:
            raise ValueError(f"Daily total would exceed Faster Payments daily limit of £{FP_MAX_DAILY:,.0f}")

        payment_id = _generate_id()
        now = _now()

        payment: dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "type": "faster_payments",
            "from_account": from_account,
            "to_account": to_account,
            "sort_code": sort_code,
            "account_number": account_number,
            "amount": amount,
            "currency": currency.upper(),
            "reference": reference or f"REF-{uuid.uuid4().hex[:8].upper()}",
            "status": "completed",
            "fees": {"fp_fee": FP_FEE, "total": FP_FEE},
            "settlement": "instant (<2 minutes)",
            "created_at": now,
            "updated_at": now,
        }

        self.FP_DB[payment_id] = payment
        logger.info("Created Faster Payment %s for user %s (%.2f GBP)", payment_id, user_id, amount)
        return copy.deepcopy(payment)

    def validate_sort_code(self, sort_code: str) -> bool:
        if not sort_code or not isinstance(sort_code, str):
            return False
        cleaned = sort_code.strip().replace("-", "").replace(" ", "")
        return bool(re.match(r"^\d{6}$", cleaned))

    def validate_account_number(self, account_number: str) -> bool:
        if not account_number or not isinstance(account_number, str):
            return False
        cleaned = account_number.strip().replace(" ", "")
        return bool(re.match(r"^\d{8}$", cleaned))

    def get_limits(self) -> dict[str, Any]:
        return {
            "max_single": FP_MAX_SINGLE,
            "max_single_formatted": f"£{FP_MAX_SINGLE:,.0f}",
            "max_daily": FP_MAX_DAILY,
            "max_daily_formatted": f"£{FP_MAX_DAILY:,.0f}",
            "currency": "GBP",
        }

    def _get_daily_total(self, user_id: str) -> float:
        today_start = _today_start()
        total = 0.0
        for record in self.FP_DB.values():
            if record["user_id"] == user_id and record["created_at"] >= today_start:
                total += record["amount"]
        return total

    def create_demo_data(self, user_id: str) -> list[str]:
        demos: list[dict[str, Any]] = [
            {
                "from_account": "12345678",
                "to_account": "87654321",
                "sort_code": "20-00-00",
                "account_number": "11111111",
                "amount": 350.00,
                "reference": "Electric bill March",
            },
            {
                "from_account": "12345678",
                "to_account": "11223344",
                "sort_code": "40-00-00",
                "account_number": "22222222",
                "amount": 1250.00,
                "reference": "Supplier payment",
            },
            {
                "from_account": "12345678",
                "to_account": "55667788",
                "sort_code": "09-01-28",
                "account_number": "33333333",
                "amount": 75.50,
                "reference": "Refund - order #10293",
            },
        ]

        ids: list[str] = []
        for demo in demos:
            payment = self.create_faster_payment(user_id=user_id, **demo)
            ids.append(payment["payment_id"])

        logger.info("Created %d demo Faster Payments for user %s", len(demos), user_id)
        return ids


def _today_start() -> float:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp()
