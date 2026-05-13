import copy
import re
import time
import uuid
from typing import Any, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)

SCT_INSTANT_LIMIT: float = 100000.0
SEPA_FEE: float = 1.0
SEPA_DD_FEE: float = 0.5

IBAN_LENGTHS_SEPA: dict[str, int] = {
    "AT": 20, "BE": 16, "BG": 22, "HR": 21, "CY": 28, "CZ": 24,
    "DK": 18, "EE": 20, "FI": 18, "FR": 27, "DE": 22, "GI": 23,
    "GR": 27, "HU": 28, "IS": 26, "IE": 22, "IT": 27, "LV": 21,
    "LI": 21, "LT": 20, "LU": 20, "MT": 31, "MC": 27, "NL": 18,
    "NO": 15, "PL": 28, "PT": 25, "RO": 24, "SK": 24, "SI": 19,
    "ES": 24, "SE": 24, "CH": 21,
}


def _generate_id(prefix: str = "sepa") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


def _now() -> float:
    return time.time()


class SEPAEngine:
    SEPA_DB: dict[str, dict[str, Any]] = {}
    MANDATE_DB: dict[str, dict[str, Any]] = {}

    def create_sepa_credit(
        self,
        user_id: str,
        from_iban: str,
        to_iban: str,
        amount: float,
        currency: str = "EUR",
        beneficiary_name: str = "",
        reference: str = "",
    ) -> dict[str, Any]:
        if not self.validate_iban(from_iban):
            raise ValueError(f"Invalid sender IBAN: {from_iban}")
        if not self.validate_iban(to_iban):
            raise ValueError(f"Invalid recipient IBAN: {to_iban}")
        if currency.upper() != "EUR":
            raise ValueError("SEPA Credit Transfer requires EUR currency")

        payment_id = _generate_id("sct")
        now = _now()
        is_instant = amount <= SCT_INSTANT_LIMIT

        payment: dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "type": "sepa_credit",
            "from_iban": from_iban,
            "to_iban": to_iban,
            "amount": amount,
            "currency": currency.upper(),
            "beneficiary_name": beneficiary_name,
            "reference": reference or f"INV-{uuid.uuid4().hex[:8].upper()}",
            "scheme": "SCT_INSTANT" if is_instant else "SCT",
            "status": "completed" if is_instant else "pending",
            "fees": {"sepa_fee": SEPA_FEE, "total": SEPA_FEE},
            "settlement_time": "instant (<10s)" if is_instant else "1 business day",
            "created_at": now,
            "updated_at": now,
        }

        self.SEPA_DB[payment_id] = payment
        logger.info(
            "Created SEPA credit %s for user %s (%.2f EUR, instant=%s)",
            payment_id, user_id, amount, is_instant,
        )
        return copy.deepcopy(payment)

    def create_sepa_direct_debit(
        self,
        user_id: str,
        mandate_id: str,
        from_iban: str,
        to_iban: str,
        amount: float,
        currency: str = "EUR",
        reference: str = "",
    ) -> dict[str, Any]:
        if not self.validate_iban(from_iban):
            raise ValueError(f"Invalid sender IBAN: {from_iban}")
        if not self.validate_iban(to_iban):
            raise ValueError(f"Invalid recipient IBAN: {to_iban}")
        if currency.upper() != "EUR":
            raise ValueError("SEPA Direct Debit requires EUR currency")

        mandate = self.MANDATE_DB.get(mandate_id)
        if mandate is None:
            raise ValueError(f"Mandate not found: {mandate_id}")
        if not mandate.get("active", False):
            raise ValueError(f"Mandate is not active: {mandate_id}")

        payment_id = _generate_id("sdd")
        now = _now()

        payment: dict[str, Any] = {
            "payment_id": payment_id,
            "user_id": user_id,
            "type": "sepa_direct_debit",
            "mandate_id": mandate_id,
            "from_iban": from_iban,
            "to_iban": to_iban,
            "amount": amount,
            "currency": currency.upper(),
            "reference": reference or f"DD-{uuid.uuid4().hex[:8].upper()}",
            "scheme": "SDD_CORE" if mandate["mandate_type"] == "core" else "SDD_B2B",
            "status": "pending",
            "fees": {"sepa_dd_fee": SEPA_DD_FEE, "total": SEPA_DD_FEE},
            "settlement_time": "1 business day",
            "created_at": now,
            "updated_at": now,
        }

        self.SEPA_DB[payment_id] = payment
        logger.info(
            "Created SEPA direct debit %s for user %s (%.2f EUR, mandate=%s)",
            payment_id, user_id, amount, mandate_id,
        )
        return copy.deepcopy(payment)

    def create_mandate(
        self,
        user_id: str,
        debtor_iban: str,
        debtor_name: str,
        creditor_name: str,
        mandate_type: str = "core",
    ) -> dict[str, Any]:
        if mandate_type not in ("core", "b2b"):
            raise ValueError(f"Invalid mandate type: {mandate_type}, must be 'core' or 'b2b'")
        if not self.validate_iban(debtor_iban):
            raise ValueError(f"Invalid debtor IBAN: {debtor_iban}")

        mandate_id = _generate_id("mand")
        now = _now()

        mandate: dict[str, Any] = {
            "mandate_id": mandate_id,
            "user_id": user_id,
            "debtor_iban": debtor_iban,
            "debtor_name": debtor_name,
            "creditor_name": creditor_name,
            "mandate_type": mandate_type,
            "active": True,
            "signed_date": now,
            "created_at": now,
        }

        self.MANDATE_DB[mandate_id] = mandate
        logger.info("Created SEPA mandate %s for %s (type=%s)", mandate_id, creditor_name, mandate_type)
        return copy.deepcopy(mandate)

    def get_mandates(self, user_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for mandate in self.MANDATE_DB.values():
            if mandate["user_id"] == user_id:
                result.append(copy.deepcopy(mandate))
        return result

    def cancel_mandate(self, mandate_id: str) -> Optional[dict[str, Any]]:
        mandate = self.MANDATE_DB.get(mandate_id)
        if mandate is None:
            return None
        mandate["active"] = False
        mandate["cancelled_at"] = _now()
        logger.info("Cancelled SEPA mandate %s", mandate_id)
        return copy.deepcopy(mandate)

    def validate_iban(self, iban: str) -> bool:
        if not iban or not isinstance(iban, str):
            return False
        cleaned = iban.strip().replace(" ", "").upper()
        country_code = cleaned[:2]
        expected_length = IBAN_LENGTHS_SEPA.get(country_code)
        if expected_length is None:
            return False
        if len(cleaned) != expected_length:
            return False
        if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", cleaned):
            return False
        reordered = cleaned[4:] + cleaned[:4]
        numeric = ""
        for ch in reordered:
            if ch.isdigit():
                numeric += ch
            else:
                numeric += str(ord(ch) - 55)
        return self._mod97(numeric) == 1

    def _mod97(self, numeric: str) -> int:
        chunks = [numeric[i:i + 9] for i in range(0, len(numeric), 9)]
        remainder = 0
        for chunk in chunks:
            remainder = int(str(remainder) + chunk) % 97
        return remainder

    def create_demo_data(self, user_id: str) -> list[str]:
        mandate = self.create_mandate(
            user_id=user_id,
            debtor_iban="DE89370400440532013000",
            debtor_name="John Doe",
            creditor_name="Utility Provider GmbH",
            mandate_type="core",
        )

        demos: list[dict[str, Any]] = [
            {
                "from_iban": "DE89370400440532013000",
                "to_iban": "FR1420041010050500013M02606",
                "amount": 2500.00,
                "beneficiary_name": "Paris Consulting SARL",
                "reference": "INV-2024-001",
            },
            {
                "from_iban": "DE89370400440532013000",
                "to_iban": "IT60X0542811101000000123456",
                "amount": 150000.00,
                "beneficiary_name": "Milano Design SPA",
                "reference": "INV-2024-002",
            },
            {
                "from_iban": "DE89370400440532013000",
                "to_iban": "ES9121000418450200051332",
                "amount": 89.99,
                "beneficiary_name": "Madrid Tech SL",
                "reference": "SUB-2024-003",
            },
        ]

        ids: list[str] = []
        for demo in demos:
            payment = self.create_sepa_credit(user_id=user_id, **demo)
            ids.append(payment["payment_id"])

        dd = self.create_sepa_direct_debit(
            user_id=user_id,
            mandate_id=mandate["mandate_id"],
            from_iban="DE89370400440532013000",
            to_iban="DE44500105123456789123",
            amount=199.99,
            reference="UTILITY-MAR-2024",
        )
        ids.append(dd["payment_id"])

        logger.info("Created %d demo SEPA transactions for user %s", len(ids), user_id)
        return ids
