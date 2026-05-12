from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

SANCTIONED_ADDRESSES: List[str] = [
    "0x1f9090aae28b8a3dceadf281b0f12828e676c326",
    "0x8576acc5c05d6ce88f4e49bf65bdf0c62f91353c",
    "0x2f7e1e4b6e3e2e3a0f9e8d7c6b5a4f3e2d1c0b1a",
    "0xa0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
    "0xc0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9",
    "1FfB8aD1b2c3D4E5F6a7B8c9D0e1F2a3B4c5D6e7",
    "1A2b3C4d5E6f7A8b9C0d1E2f3A4b5C6d7E8f9A0b",
    "8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b",
    "raddr1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
    "addr1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
]

FLAG_THRESHOLD_USD = 10000.0

HIGH_RISK_COUNTRIES = [
    "Iran",
    "North Korea",
    "Syria",
    "Russia",
    "Myanmar",
    "Cuba",
    "Venezuela",
    "Yemen",
]

MOCK_VASP_REGISTRY: Dict[str, Dict[str, str]] = {
    "Binance": {"lei": "5493001KJTIIGC8Y1R12", "jurisdiction": "Cayman Islands", "regulator": "FIU Cayman"},
    "Coinbase": {"lei": "5493007PFE2QWHCL9V21", "jurisdiction": "United States", "regulator": "FinCEN"},
    "Kraken": {"lei": "5493006MZB84EKFQYH36", "jurisdiction": "United States", "regulator": "FinCEN"},
    "Gemini": {"lei": "5493008Q8M5XKQJNX56", "jurisdiction": "United States", "regulator": "NYDFS"},
}


def _is_sanctioned(address: str) -> bool:
    addr_lower = address.lower()
    return any(addr_lower == sa.lower() for sa in SANCTIONED_ADDRESSES)


def _calculate_amount_risk(amount_usd: float) -> int:
    if amount_usd <= 1000:
        return 5
    if amount_usd <= 5000:
        return 15
    if amount_usd <= 10000:
        return 30
    if amount_usd <= 50000:
        return 55
    if amount_usd <= 100000:
        return 75
    return 95


def _calculate_currency_risk(currency: str) -> int:
    privacy_coins = {"XMR", "ZEC", "DASH", "LTC"}
    return 40 if currency.upper() in privacy_coins else 5


def _calculate_network_risk(network: str) -> int:
    mixers = {"tornado_cash", "wasabi", "coinjoin"}
    return 50 if network.lower() in mixers else 5


class CryptoComplianceEngine:
    def __init__(self) -> None:
        self.SCREENING_DB: Dict[str, Dict[str, Any]] = {}

    def screen_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        tx_id = tx_data.get("tx_id", str(uuid.uuid4()))
        amount = tx_data.get("amount", 0.0)
        currency = tx_data.get("currency", "USD")
        from_address = tx_data.get("from", "")
        to_address = tx_data.get("to", "")
        network = tx_data.get("network", "ethereum")

        from .wallets import MOCK_USD_RATES
        usd_rate = MOCK_USD_RATES.get(currency.upper(), 1.0)
        amount_usd = amount * usd_rate

        risk_score = self.calculate_risk_score(amount, currency, from_address, to_address, network)

        flags: List[str] = []
        requires_approval = False
        reason = ""

        if _is_sanctioned(from_address):
            flags.append("SANCTIONED_SENDER")
            risk_score = max(risk_score, 95)
            requires_approval = True
            reason = "Sender address is on sanctions list"

        if _is_sanctioned(to_address):
            flags.append("SANCTIONED_RECIPIENT")
            risk_score = max(risk_score, 95)
            requires_approval = True
            reason = "Recipient address is on sanctions list"

        if amount_usd > FLAG_THRESHOLD_USD:
            flags.append("HIGH_VALUE")
            risk_score = max(risk_score, 60)
            if amount_usd > 100000:
                requires_approval = True
                reason = f"Transaction amount ${amount_usd:,.2f} exceeds $100,000 threshold"

        if network.lower() in ("tornado_cash",):
            flags.append("MIXER_USAGE")
            risk_score = max(risk_score, 85)
            requires_approval = True
            reason = "Transaction involves a cryptocurrency mixer"

        screen_id = str(uuid.uuid4())
        result = {
            "screen_id": screen_id,
            "tx_id": tx_id,
            "risk_score": min(risk_score, 100),
            "risk_level": self._risk_level(risk_score),
            "flags": flags,
            "requires_approval": requires_approval,
            "reason": reason,
            "amount_usd": round(amount_usd, 2),
            "currency": currency.upper(),
            "from": from_address,
            "to": to_address,
            "network": network,
            "screened_at": time.time(),
        }
        self.SCREENING_DB[screen_id] = result
        return result

    def check_address(self, address: str, currency: str) -> Dict[str, Any]:
        addr_lower = address.lower()
        sanctioned = _is_sanctioned(address)
        matched_address = ""
        if sanctioned:
            matched_address = next(
                (sa for sa in SANCTIONED_ADDRESSES if sa.lower() == addr_lower), ""
            )
        return {
            "address": address,
            "currency": currency.upper(),
            "sanctioned": sanctioned,
            "matched_address": matched_address,
            "risk_level": "high" if sanctioned else "low",
            "country_restrictions": HIGH_RISK_COUNTRIES if sanctioned else [],
        }

    def get_sanctioned_addresses(self) -> List[str]:
        return SANCTIONED_ADDRESSES.copy()

    def calculate_risk_score(
        self,
        amount: float,
        currency: str,
        from_address: str,
        to_address: str,
        network: str,
    ) -> int:
        from .wallets import MOCK_USD_RATES
        usd_rate = MOCK_USD_RATES.get(currency.upper(), 1.0)
        amount_usd = amount * usd_rate

        amount_risk = _calculate_amount_risk(amount_usd)
        currency_risk = _calculate_currency_risk(currency)
        network_risk = _calculate_network_risk(network)
        sanctions_risk = 80 if _is_sanctioned(from_address) or _is_sanctioned(to_address) else 0

        score = (amount_risk * 0.35) + (currency_risk * 0.15) + (network_risk * 0.15) + (sanctions_risk * 0.35)
        return int(score)

    def create_travel_rule_data(self, user_id: str, transaction_id: str) -> Dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "originating_vasp": "Ask IRA Exchange",
            "originating_vasp_lei": "549300ZZZZZZZZZZZZ12",
            "beneficiary_vasp": "External Exchange",
            "beneficiary_vasp_lei": "UNKNOWN",
            "originator": {
                "user_id": user_id,
                "name": "REDACTED_PER_PRIVACY",
                "jurisdiction": "International",
                "account_type": "HOSTED_WALLET",
            },
            "beneficiary": {
                "name": "REDACTED_PER_PRIVACY",
                "jurisdiction": "International",
                "account_type": "EXTERNAL_WALLET",
            },
            "compliance_data": {
                "fatf_recommendation": 16,
                "travel_rule_threshold_usd": 3000,
                "data_encrypted": True,
                "encryption_standard": "ISO 20022",
            },
            "generated_at": time.time(),
        }

    def create_demo_data(self) -> List[Dict[str, Any]]:
        demo_screens = [
            {
                "amount": 500.0,
                "currency": "ETH",
                "from": "0x1234567890abcdef1234567890abcdef12345678",
                "to": "0xabcdef1234567890abcdef1234567890abcdef12",
                "network": "ethereum",
            },
            {
                "amount": 50000.0,
                "currency": "USDT",
                "from": "0x1f9090aae28b8a3dceadf281b0f12828e676c326",
                "to": "0x8576acc5c05d6ce88f4e49bf65bdf0c62f91353c",
                "network": "erc20",
            },
        ]
        results: List[Dict[str, Any]] = []
        for data in demo_screens:
            data["tx_id"] = str(uuid.uuid4())
            result = self.screen_transaction(data)
            results.append(result)
        return results

    def _risk_level(self, score: int) -> str:
        if score < 25:
            return "low"
        if score < 50:
            return "medium"
        if score < 75:
            return "elevated"
        return "high"
