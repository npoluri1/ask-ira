import copy
import re
import time
import uuid
from typing import Any

from src.config.logging import get_logger

logger = get_logger(__name__)

ACH_FEE: float = 0.50

SEC_CODES: dict[str, str] = {
    "CCD": "Corporate Credit or Debit",
    "PPD": "Prearranged Payment and Deposit",
    "WEB": "Internet Initiated Entry",
    "TEL": "Telephone Initiated Entry",
    "ARC": "Accounts Receivable Entry",
    "BOC": "Back Office Conversion",
    "POP": "Point of Purchase Entry",
    "RCK": "Re-presented Check Entry",
}

SETTLEMENT_TIMELINES: dict[str, str] = {
    "same_day": "Same business day (cutoff varies by bank, typically 2-5 PM ET)",
    "standard": "1-2 business days",
}


def _generate_id(prefix: str = "ach") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


def _now() -> float:
    return time.time()


class AHEngine:
    ACH_DB: dict[str, dict[str, Any]] = {}

    def create_ach_credit(
        self,
        user_id: str,
        from_routing: str,
        from_account: str,
        to_routing: str,
        to_account: str,
        amount: float,
        currency: str = "USD",
        description: str = "",
        company_name: str = "",
        company_entry_description: str = "",
    ) -> dict[str, Any]:
        if currency.upper() != "USD":
            raise ValueError("ACH requires USD currency")
        if not self.validate_routing(from_routing):
            raise ValueError(f"Invalid source routing number: {from_routing}")
        if not self.validate_routing(to_routing):
            raise ValueError(f"Invalid destination routing number: {to_routing}")

        payment_id = _generate_id("ach_cr")
        now = _now()

        payment: dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "type": "ach_credit",
            "from_routing": from_routing,
            "from_account": from_account,
            "to_routing": to_routing,
            "to_account": to_account,
            "amount": amount,
            "currency": currency.upper(),
            "description": description or "ACH credit transfer",
            "company_name": company_name or "Automated Clearing House",
            "company_entry_description": company_entry_description or "ACH CREDIT",
            "sec_code": self._determine_sec_code(description),
            "status": "pending",
            "fees": {"ach_fee": ACH_FEE, "total": ACH_FEE},
            "settlement": "standard (1-2 business days)",
            "created_at": now,
            "updated_at": now,
        }

        self.ACH_DB[payment_id] = payment
        logger.info("Created ACH credit %s for user %s (%.2f USD)", payment_id, user_id, amount)
        return copy.deepcopy(payment)

    def create_ach_debit(
        self,
        user_id: str,
        from_routing: str,
        from_account: str,
        to_routing: str,
        to_account: str,
        amount: float,
        currency: str = "USD",
        description: str = "",
    ) -> dict[str, Any]:
        if currency.upper() != "USD":
            raise ValueError("ACH requires USD currency")
        if not self.validate_routing(from_routing):
            raise ValueError(f"Invalid source routing number: {from_routing}")
        if not self.validate_routing(to_routing):
            raise ValueError(f"Invalid destination routing number: {to_routing}")

        payment_id = _generate_id("ach_db")
        now = _now()

        payment: dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "type": "ach_debit",
            "from_routing": from_routing,
            "from_account": from_account,
            "to_routing": to_routing,
            "to_account": to_account,
            "amount": amount,
            "currency": currency.upper(),
            "description": description or "ACH debit transfer",
            "sec_code": self._determine_sec_code(description),
            "status": "pending",
            "fees": {"ach_fee": ACH_FEE, "total": ACH_FEE},
            "settlement": "standard (1-2 business days)",
            "created_at": now,
            "updated_at": now,
        }

        self.ACH_DB[payment_id] = payment
        logger.info("Created ACH debit %s for user %s (%.2f USD)", payment_id, user_id, amount)
        return copy.deepcopy(payment)

    def validate_routing(self, routing_number: str) -> bool:
        if not routing_number or not isinstance(routing_number, str):
            return False
        cleaned = routing_number.strip()
        if not re.match(r"^\d{9}$", cleaned):
            return False
        digits = [int(d) for d in cleaned]
        checksum = (
            3 * (digits[0] + digits[3] + digits[6])
            + 7 * (digits[1] + digits[4] + digits[7])
            + digits[2] + digits[5] + digits[8]
        )
        return checksum % 10 == 0

    def _determine_sec_code(self, description: str) -> str:
        desc_lower = description.lower()
        if "web" in desc_lower or "internet" in desc_lower or "online" in desc_lower:
            return "WEB"
        if "tel" in desc_lower or "phone" in desc_lower or "call" in desc_lower:
            return "TEL"
        if "pos" in desc_lower or "purchase" in desc_lower:
            return "POP"
        return "CCD"

    def get_ach_standard_entry_class_codes(self) -> dict[str, str]:
        return copy.deepcopy(SEC_CODES)

    def get_settlement_timeline(self) -> dict[str, str]:
        return copy.deepcopy(SETTLEMENT_TIMELINES)

    def create_demo_data(self, user_id: str) -> list[str]:
        demos: list[dict[str, Any]] = [
            {
                "from_routing": "021000021",
                "from_account": "123456789",
                "to_routing": "071000013",
                "to_account": "987654321",
                "amount": 12500.00,
                "description": "Payroll processing - March 2024",
                "company_name": "Acme Corp Inc.",
                "company_entry_description": "PAYROLL",
            },
            {
                "from_routing": "021000021",
                "from_account": "123456789",
                "to_routing": "026009593",
                "to_account": "456789123",
                "amount": 3500.00,
                "description": "Vendor payment - Cloud services",
                "company_name": "Acme Corp Inc.",
                "company_entry_description": "VENDOR PAY",
            },
            {
                "from_routing": "021000021",
                "from_account": "123456789",
                "to_routing": "122105278",
                "to_account": "789123456",
                "amount": 750.00,
                "description": "Internet initiated payment",
                "company_name": "Acme Corp Inc.",
                "company_entry_description": "WEB PYMT",
            },
        ]

        ids: list[str] = []
        for demo in demos:
            payment = self.create_ach_credit(user_id=user_id, **demo)
            ids.append(payment["payment_id"])

        debit = self.create_ach_debit(
            user_id=user_id,
            from_routing="021000021",
            from_account="123456789",
            to_routing="071000013",
            to_account="555555555",
            amount=250.00,
            description="Utility payment - WEB",
        )
        ids.append(debit["payment_id"])

        logger.info("Created %d demo ACH transactions for user %s", len(ids), user_id)
        return ids
