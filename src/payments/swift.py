import uuid
import time
import copy
import re
from typing import Any, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)

SWIFT_FEE: float = 25.0
INTERMEDIARY_FEE_PER_BANK: float = 15.0
CURRENCY_CONVERSION_FEE_PERCENT: float = 0.005

IBAN_LENGTHS: dict[str, int] = {
    "AL": 28, "AD": 24, "AT": 20, "AZ": 28, "BH": 22, "BY": 28, "BE": 16,
    "BA": 20, "BR": 29, "BG": 22, "CR": 22, "HR": 21, "CY": 28, "CZ": 24,
    "DK": 18, "DO": 28, "EE": 20, "FO": 18, "FI": 18, "FR": 27, "GE": 22,
    "DE": 22, "GI": 23, "GR": 27, "GL": 18, "GT": 28, "HU": 28, "IS": 26,
    "IE": 22, "IL": 23, "IT": 27, "JO": 30, "KZ": 20, "XK": 20, "KW": 30,
    "LV": 21, "LB": 28, "LI": 21, "LT": 20, "LU": 20, "MK": 19, "MT": 31,
    "MR": 27, "MU": 30, "MD": 24, "MC": 27, "ME": 22, "NL": 18, "NO": 15,
    "PK": 24, "PS": 29, "PL": 28, "PT": 25, "QA": 29, "RO": 24, "LC": 32,
    "SM": 27, "ST": 25, "SA": 24, "RS": 22, "SC": 31, "SK": 24, "SI": 19,
    "ES": 24, "SE": 24, "CH": 21, "TL": 23, "TN": 24, "TR": 26, "UA": 29,
    "AE": 23, "GB": 22, "VG": 24, "VA": 22,
}

SWIFT_MEMBER_BANKS: list[dict[str, str]] = [
    {"bic": "BOFAUS3N", "name": "Bank of America", "country": "US", "city": "New York"},
    {"bic": "CITIUS33", "name": "Citibank N.A.", "country": "US", "city": "New York"},
    {"bic": "JPMORGAN", "name": "JPMorgan Chase", "country": "US", "city": "New York"},
    {"bic": "WFBIUS6S", "name": "Wells Fargo Bank", "country": "US", "city": "San Francisco"},
    {"bic": "GSGCUS33", "name": "Goldman Sachs", "country": "US", "city": "New York"},
    {"bic": "DEUTDEFF", "name": "Deutsche Bank", "country": "DE", "city": "Frankfurt"},
    {"bic": "COBADEFF", "name": "Commerzbank", "country": "DE", "city": "Frankfurt"},
    {"bic": "BNPAFRPP", "name": "BNP Paribas", "country": "FR", "city": "Paris"},
    {"bic": "SOGEFRPP", "name": "Societe Generale", "country": "FR", "city": "Paris"},
    {"bic": "BARCGB22", "name": "Barclays Bank", "country": "GB", "city": "London"},
    {"bic": "HSBCGB2L", "name": "HSBC Bank", "country": "GB", "city": "London"},
    {"bic": "LOYDGB21", "name": "Lloyds Bank", "country": "GB", "city": "London"},
    {"bic": "UBSWCHZH", "name": "UBS Switzerland", "country": "CH", "city": "Zurich"},
    {"bic": "CRESCHZZ", "name": "Credit Suisse", "country": "CH", "city": "Zurich"},
    {"bic": "ABNANL2A", "name": "ABN AMRO Bank", "country": "NL", "city": "Amsterdam"},
    {"bic": "INGBNL2A", "name": "ING Bank", "country": "NL", "city": "Amsterdam"},
    {"bic": "MHCBJPJT", "name": "Mizuho Bank", "country": "JP", "city": "Tokyo"},
    {"bic": "SMBCJPJT", "name": "Sumitomo Mitsui Bank", "country": "JP", "city": "Tokyo"},
    {"bic": "DBSSSGSG", "name": "DBS Bank", "country": "SG", "city": "Singapore"},
    {"bic": "UOVBSGSP", "name": "United Overseas Bank", "country": "SG", "city": "Singapore"},
]


def _generate_swift_id() -> str:
    return f"mt103_{uuid.uuid4().hex[:20]}"


def _now() -> float:
    return time.time()


def _add_business_days(start: float, days: int) -> float:
    from datetime import datetime, timedelta
    dt = datetime.fromtimestamp(start)
    added = 0
    while added < days:
        dt += timedelta(days=1)
        if dt.weekday() < 5:
            added += 1
    return dt.timestamp()


class SWIFTEngine:
    SWIFT_DB: dict[str, dict[str, Any]] = {}

    def create_mt103(
        self,
        user_id: str,
        sender_account: str,
        receiver_bic: str,
        receiver_account: str,
        amount: float,
        currency: str,
        beneficiary_name: str,
        beneficiary_address: str = "",
        intermediary_bic: Optional[str] = None,
        purpose_code: str = "1000",
    ) -> dict[str, Any]:
        swift_id = _generate_swift_id()
        now = _now()
        value_date = _add_business_days(now, 2)

        charges_type = "SHA" if not intermediary_bic else "BEN"

        sending_institution = "CHASUS33,JPMorgan Chase Bank,New York,US"
        ordering_customer = f"{user_id},{sender_account}"
        beneficiary_customer = f"{beneficiary_name},{beneficiary_address},{receiver_account}"
        intermediary_info = f"{intermediary_bic},Intermediary Bank,,"
        if intermediary_bic:
            bank = self._find_bank_by_bic(intermediary_bic)
            if bank:
                intermediary_info = f"{intermediary_bic},{bank['name']},{bank['city']},{bank['country']}"

        receiver_bank = self._find_bank_by_bic(receiver_bic)
        receiver_name = receiver_bank["name"] if receiver_bank else receiver_bic

        message: dict[str, Any] = {
            "swift_id": swift_id,
            "user_id": user_id,
            "mt_type": "MT103",
            "fields": {
                "20": swift_id,
                "23B": "CRED",
                "23E": charges_type,
                "32A": f"{value_date}{currency}{amount:.2f}",
                "33B": f"{currency}{amount:.2f}",
                "50K": ordering_customer,
                "52A": sending_institution,
                "56A": intermediary_info,
                "57A": f"{receiver_bic},{receiver_name},,",
                "59": beneficiary_customer,
                "70": purpose_code,
                "71A": charges_type,
                "72": f"/REC/{receiver_account}",
            },
            "sender_account": sender_account,
            "receiver_bic": receiver_bic,
            "receiver_account": receiver_account,
            "receiver_name": receiver_name,
            "amount": amount,
            "currency": currency.upper(),
            "beneficiary_name": beneficiary_name,
            "beneficiary_address": beneficiary_address,
            "intermediary_bic": intermediary_bic,
            "purpose_code": purpose_code,
            "value_date": value_date,
            "charges_type": charges_type,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }

        tracking_status: list[dict[str, Any]] = [
            {"location": "Sending Institution", "timestamp": now, "status": "processed"},
            {"location": "SWIFT Network", "timestamp": now + 1800, "status": "in_transit"},
        ]
        if intermediary_bic:
            tracking_status.append(
                {"location": "Intermediary Bank A", "timestamp": now + 3600, "status": "in_transit"}
            )
        tracking_status.append(
            {"location": "Central Bank", "timestamp": now + 7200, "status": "pending"}
        )
        tracking_status.append(
            {"location": receiver_name, "timestamp": now + 86400, "status": "pending"}
        )

        self.SWIFT_DB[swift_id] = {
            "message": message,
            "tracking": {"statuses": tracking_status, "current_location": "Sending Institution"},
        }

        logger.info(
            "Created SWIFT MT103 %s for user %s (%.2f %s via %s)",
            swift_id, user_id, amount, currency, receiver_bic,
        )
        return message

    def track_message(self, swift_id: str) -> Optional[dict[str, Any]]:
        record = self.SWIFT_DB.get(swift_id)
        if record is None:
            return None
        return copy.deepcopy(record)

    def get_participating_banks(self) -> list[dict[str, str]]:
        return copy.deepcopy(SWIFT_MEMBER_BANKS)

    def calculate_swift_fees(
        self,
        amount: float,
        currency: str,
        intermediary_banks: int = 0,
    ) -> dict[str, Any]:
        swift_fee = SWIFT_FEE
        inter_fee = intermediary_banks * INTERMEDIARY_FEE_PER_BANK
        conv_fee = round(amount * CURRENCY_CONVERSION_FEE_PERCENT, 2)
        total = round(swift_fee + inter_fee + conv_fee, 2)

        return {
            "swift_fee": swift_fee,
            "intermediary_bank_fees": inter_fee,
            "intermediary_bank_count": intermediary_banks,
            "currency_conversion_fee": conv_fee,
            "total_fee": total,
            "currency": currency.upper(),
        }

    def validate_bic(self, bic: str) -> bool:
        if not bic or not isinstance(bic, str):
            return False
        cleaned = bic.strip().upper()
        if len(cleaned) not in (8, 11):
            return False
        pattern = r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$"
        return bool(re.match(pattern, cleaned))

    def validate_iban(self, iban: str) -> bool:
        if not iban or not isinstance(iban, str):
            return False
        cleaned = iban.strip().replace(" ", "").upper()
        country_code = cleaned[:2]
        expected_length = IBAN_LENGTHS.get(country_code)
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
        if len(numeric) > 50:
            return self._mod97_large(numeric) == 1
        return int(numeric) % 97 == 1

    def _mod97_large(self, numeric: str) -> int:
        chunks = [numeric[i:i + 9] for i in range(0, len(numeric), 9)]
        remainder = 0
        for chunk in chunks:
            remainder = int(str(remainder) + chunk) % 97
        return remainder

    def _find_bank_by_bic(self, bic: str) -> Optional[dict[str, str]]:
        for bank in SWIFT_MEMBER_BANKS:
            if bank["bic"] == bic:
                return bank
        return None

    def create_demo_data(self, user_id: str, account_id: str = "ACC-12345") -> list[str]:
        demos: list[dict[str, Any]] = [
            {
                "sender_account": account_id,
                "receiver_bic": "DEUTDEFF",
                "receiver_account": "DE89370400440532013000",
                "amount": 25000.00,
                "currency": "EUR",
                "beneficiary_name": "EuroTech GmbH",
                "beneficiary_address": "Frankfurter Allee 100, Berlin",
                "intermediary_bic": "BOFAUS3N",
                "purpose_code": "1000",
            },
            {
                "sender_account": account_id,
                "receiver_bic": "HSBCGB2L",
                "receiver_account": "GB29NWBK60161331926819",
                "amount": 15000.00,
                "currency": "GBP",
                "beneficiary_name": "London Trading Ltd",
                "beneficiary_address": "Canary Wharf, London",
                "intermediary_bic": None,
                "purpose_code": "1010",
            },
            {
                "sender_account": account_id,
                "receiver_bic": "MHCBJPJT",
                "receiver_account": "JP911000123456789",
                "amount": 5000000.00,
                "currency": "JPY",
                "beneficiary_name": "Tokyo Trading KK",
                "beneficiary_address": "Marunouchi 1-3, Tokyo",
                "intermediary_bic": "CITIUS33",
                "purpose_code": "2000",
            },
        ]

        ids: list[str] = []
        for demo in demos:
            msg = self.create_mt103(user_id=user_id, **demo)
            ids.append(msg["swift_id"])

        logger.info("Created %d demo SWIFT transfers for user %s", len(demos), user_id)
        return ids
