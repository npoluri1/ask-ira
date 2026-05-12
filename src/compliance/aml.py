import time
import uuid
from decimal import Decimal
from typing import Any

AML_DB: dict[str, list[dict]] = {}

MOCK_PEP_LIST: list[dict[str, str]] = [
    {"name": "Vladimir Petrov", "country": "Russia", "position": "Former Head of State"},
    {"name": "Li Wei", "country": "China", "position": "Senior Minister"},
    {"name": "Ahmed Al-Rashid", "country": "Saudi Arabia", "position": "Royal Family Member"},
    {"name": "Maria Silva", "country": "Brazil", "position": "Cabinet Minister"},
    {"name": "John Mwangi", "country": "Kenya", "position": "Central Bank Governor"},
]

HIGH_RISK_COUNTRIES: list[str] = [
    "Iran", "North Korea", "Syria", "Crimea", "Russia", "Belarus",
    "Myanmar", "Venezuela", "Yemen", "Afghanistan", "Iraq", "Libya",
    "Somalia", "South Sudan", "Sudan",
]

HIGH_RISK_COUNTRY_CODES: dict[str, str] = {
    "Iran": "IR", "North Korea": "KP", "Syria": "SY", "Crimea": "UA-43",
    "Russia": "RU", "Belarus": "BY", "Myanmar": "MM", "Venezuela": "VE",
    "Yemen": "YE", "Afghanistan": "AF", "Iraq": "IQ", "Libya": "LY",
    "Somalia": "SO", "South Sudan": "SS", "Sudan": "SD",
}

FINCEN_COUNTRIES: list[str] = ["US", "GB", "DE", "FR", "IT", "CA", "AU", "JP", "SG", "CH", "NL", "HK"]
FCA_COUNTRIES: list[str] = ["GB", "DE", "FR", "IT", "ES", "NL", "CH", "SG", "HK", "AE", "US"]
FATF_LIST: list[str] = ["IR", "KP", "MM", "BY"]

STRUCTURING_THRESHOLD: float = 10000.0
STRUCTURING_WINDOW_HOURS: int = 24
CTR_THRESHOLD: float = 10000.0


class AMLEngine:
    def screen_user(
        self,
        user_id: str,
        name: str,
        date_of_birth: str,
        nationality: str,
        country_of_residence: str,
    ) -> dict[str, Any]:
        flags: list[str] = []
        risk_score: int = 0

        name_lower = name.lower()
        for pep in MOCK_PEP_LIST:
            if pep["name"].lower() in name_lower or name_lower in pep["name"].lower():
                flags.append(f"PEP match: {pep['name']} ({pep['position']})")
                risk_score += 40

        if nationality in HIGH_RISK_COUNTRIES or country_of_residence in HIGH_RISK_COUNTRIES:
            flags.append(f"High-risk jurisdiction: {nationality}/{country_of_residence}")
            risk_score += 25

        if country_of_residence in HIGH_RISK_COUNTRIES:
            flags.append("Country of residence is high-risk")
            risk_score += 15

        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        result: dict[str, Any] = {
            "screening_id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "nationality": nationality,
            "country_of_residence": country_of_residence,
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "flags": flags,
            "requires_enhanced_due_diligence": risk_level in ("high", "critical"),
            "screened_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if user_id not in AML_DB:
            AML_DB[user_id] = []
        AML_DB[user_id].append(result)
        return result

    def screen_transaction(
        self,
        user_id: str,
        amount: float,
        currency: str,
        counterparty: str,
        country: str,
    ) -> dict[str, Any]:
        flags: list[str] = []
        regulatory_obligations: list[str] = []

        if amount >= CTR_THRESHOLD:
            flags.append(f"Amount ${amount:,.2f} exceeds CTR threshold of ${CTR_THRESHOLD:,.2f}")
            regulatory_obligations.append("CTR")

        if country in HIGH_RISK_COUNTRIES:
            flags.append(f"High-risk country: {country}")
            regulatory_obligations.append("EDD")

        if amount >= 50000:
            flags.append("Large transaction requiring enhanced scrutiny")
            regulatory_obligations.append("SAR")

        if amount >= 100000:
            flags.append("Very large transaction - mandatory reporting")
            regulatory_obligations.append("SAR")

        if amount < CTR_THRESHOLD and amount >= CTR_THRESHOLD * 0.9:
            flags.append("Near-threshold transaction - potential structuring indicator")
            regulatory_obligations.append("SAR")

        if regulatory_obligations:
            decision = "review"
        elif any(f.startswith("Amount") for f in flags):
            decision = "review"
        else:
            decision = "allow"

        result: dict[str, Any] = {
            "screen_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "counterparty": counterparty,
            "country": country,
            "decision": decision,
            "reason": "; ".join(flags) if flags else "No issues detected",
            "flags": flags,
            "regulatory_obligations": regulatory_obligations,
            "screened_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if user_id not in AML_DB:
            AML_DB[user_id] = []
        AML_DB[user_id].append(result)
        return result

    def get_high_risk_countries(self) -> list[str]:
        return HIGH_RISK_COUNTRIES.copy()

    def get_screening_history(self, user_id: str) -> list[dict[str, Any]]:
        return AML_DB.get(user_id, [])

    def file_sar(
        self, user_id: str, transaction_id: str, reason: str, details: str
    ) -> dict[str, Any]:
        sar = {
            "sar_id": f"SAR-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "transaction_id": transaction_id,
            "reason": reason,
            "details": details,
            "filing_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "regulatory_body": "FinCEN" if "US" in reason or "CTR" in reason else "FCA",
            "status": "filed",
        }
        if user_id not in AML_DB:
            AML_DB[user_id] = []
        AML_DB[user_id].append(sar)
        return sar

    def check_structuring(self, transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        threshold = STRUCTURING_THRESHOLD
        window_seconds = STRUCTURING_WINDOW_HOURS * 3600

        grouped: dict[str, list[dict[str, Any]]] = {}
        for txn in transactions:
            key = txn.get("user_id", "unknown")
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(txn)

        for user_id, txns in grouped.items():
            txns_sorted = sorted(txns, key=lambda x: x.get("timestamp", ""))
            i = 0
            while i < len(txns_sorted):
                window_txns: list[dict[str, Any]] = [txns_sorted[i]]
                j = i + 1
                base_time_str = txns_sorted[i].get("timestamp", "")
                try:
                    base_ts = time.mktime(time.strptime(base_time_str, "%Y-%m-%dT%H:%M:%SZ"))
                except (ValueError, TypeError):
                    base_ts = time.time()
                while j < len(txns_sorted):
                    next_time_str = txns_sorted[j].get("timestamp", "")
                    try:
                        next_ts = time.mktime(time.strptime(next_time_str, "%Y-%m-%dT%H:%M:%SZ"))
                    except (ValueError, TypeError):
                        next_ts = time.time()
                    if next_ts - base_ts <= window_seconds:
                        window_txns.append(txns_sorted[j])
                        j += 1
                    else:
                        break
                if len(window_txns) >= 3:
                    total = sum(t.get("amount", 0) for t in window_txns)
                    under_threshold = all(t.get("amount", 0) < threshold for t in window_txns)
                    if under_threshold and total >= threshold * 0.75:
                        alerts.append({
                            "user_id": user_id,
                            "type": "structuring_alert",
                            "transaction_count": len(window_txns),
                            "total_amount": round(total, 2),
                            "threshold": threshold,
                            "window_hours": STRUCTURING_WINDOW_HOURS,
                            "transactions": [t.get("transaction_id", t.get("id", "")) for t in window_txns],
                            "detected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "severity": "high" if total >= threshold else "medium",
                        })
                i = j if j > i else i + 1

        return alerts

    def create_demo_data(self, user_id: str):
        if AML_DB.get(user_id):
            return
        self.screen_user(user_id, "John Doe", "1990-01-15", "US", "US")
        self.screen_user(user_id, "Li Wei", "1975-06-20", "China", "China")
        self.screen_user(user_id, "Ahmed Al-Rashid", "1960-03-10", "Saudi Arabia", "AE")
        self.screen_transaction(user_id, 5000, "USD", "Acme Corp", "US")
        self.screen_transaction(user_id, 15000, "EUR", "Offshore Ltd", "Panama")
        self.screen_transaction(user_id, 9500, "USD", "Shell Co", "Iran")
