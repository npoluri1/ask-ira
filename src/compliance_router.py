import time
from typing import Any

COUNTRY_COMPLIANCE: dict[str, dict] = {
    "US": {
        "regulators": ["FinCEN", "SEC", "OFAC", "NYDFS"],
        "kyc_level_required": 2,
        "aml_checks": ["ofac", "fincen_314b", "pep", "adverse_media"],
        "sar_threshold": 10000,
        "ctr_threshold": 10000,
        "msb_threshold": 2000,
        "data_retention_years": 5,
        "privacy_law": "CCPA",
        "reporting": ["FinCEN SAR", "CTR", "FBAR"],
        "crypto_rules": ["FinCEN Travel Rule", "NYDFS Part 500", "BSA for VASPs"],
        "insurance_rules": ["State Insurance Dept Regs", "NAIC Standards"],
        "restrictions": ["No Iran", "No North Korea", "No Crimea", "No Syria"],
    },
    "UK": {
        "regulators": ["FCA", "PRA"],
        "kyc_level_required": 2,
        "aml_checks": ["ofsi", "pep", "adverse_media", "sanctions"],
        "sar_threshold": 10000,
        "data_retention_years": 5,
        "privacy_law": "UK GDPR",
        "reporting": ["NCA SAR", "FCA REP"],
        "crypto_rules": ["FCA Cryptoasset Registration", "Travel Rule"],
        "insurance_rules": ["Solvency II", "FCA PERG", "SM&CR"],
        "restrictions": ["SCA for payments > £30"],
    },
    "EU": {
        "regulators": ["EBA", "ECB", "National Regulators"],
        "kyc_level_required": 2,
        "aml_checks": ["eu_sanctions", "fatf", "pep", "adverse_media"],
        "sar_threshold": 15000,
        "data_retention_years": 5,
        "privacy_law": "GDPR",
        "reporting": ["FIU STR", "BaFin (DE)", "ACPR (FR)"],
        "crypto_rules": ["MiCA", "Travel Rule", "PSD2/PSD3"],
        "insurance_rules": ["Solvency II", "EIOPA Guidelines", "AI Act"],
        "restrictions": ["SCA all payments", "DORA compliance"],
    },
    "UAE": {
        "regulators": ["CBUAE", "DFSA (DIFC)", "ADGM FSRA"],
        "kyc_level_required": 2,
        "aml_checks": ["ofac", "un_sanctions", "uae_local", "pep"],
        "sar_threshold": 55000,
        "data_retention_years": 5,
        "privacy_law": "DIFC Data Protection / UAE PDPL",
        "reporting": ["CBUAE STR", "GOAM Reporting"],
        "crypto_rules": ["VARA Licensing", "Travel Rule", "CBUAE Token Regs"],
        "insurance_rules": ["IA Circulars", "CBUAE Insurance Regs"],
        "restrictions": ["No Israeli transactions", "AML Federal Decree 20"],
    },
    "SG": {
        "regulators": ["MAS"],
        "kyc_level_required": 2,
        "aml_checks": ["mas_sanctions", "un_sanctions", "fatf", "pep"],
        "sar_threshold": 20000,
        "data_retention_years": 5,
        "privacy_law": "PDPA",
        "reporting": ["STRO Suspicious Transaction"],
        "crypto_rules": ["PS Act License", "Notice 626 AML", "Travel Rule"],
        "insurance_rules": ["Insurance Act Cap 142", "RBC 2", "MAS TRM"],
        "restrictions": ["MAS Notice 626 compliance"],
    },
    "HK": {
        "regulators": ["HKMA", "IA", "SFC"],
        "kyc_level_required": 2,
        "aml_checks": ["hkma_guidelines", "un_sanctions", "pep"],
        "sar_threshold": 0,
        "reporting_days": 15,
        "data_retention_years": 7,
        "privacy_law": "PDPO",
        "reporting": ["HKMA Suspicious Transaction", "SFC Licensing"],
        "crypto_rules": ["SFC Virtual Asset Guidelines", "Travel Rule"],
        "insurance_rules": ["IA Cap 41", "Insurance Ordinance"],
    },
    "IN": {
        "regulators": ["RBI", "IRDAI", "SEBI"],
        "kyc_level_required": 3,
        "kyc_docs": ["Aadhaar", "PAN", "Voter ID", "Passport"],
        "aml_checks": ["unsc_sanctions", "fatf", "domestic_watchlist"],
        "sar_threshold": 1000000,
        "data_retention_years": 10,
        "privacy_law": "DPDP 2023",
        "reporting": ["FIU-IND STR", "RBI Reporting"],
        "crypto_rules": ["RBI Crypto Guidelines", "VDA Tax Rules"],
        "insurance_rules": ["IRDAI Protection Regs", "ULIP Caps"],
        "restrictions": ["Data localization required", "No anonymous crypto"],
    },
    "JP": {
        "regulators": ["FSA", "JFSA"],
        "kyc_level_required": 2,
        "aml_checks": ["fsa_sanctions", "fatf", "pep"],
        "sar_threshold": 0,
        "data_retention_years": 7,
        "privacy_law": "APPI",
        "reporting": ["FSA Suspicious Transaction"],
        "crypto_rules": ["Payment Services Act", "Travel Rule", "Cold Wallet Custody"],
        "insurance_rules": ["Insurance Business Act", "JFSA Guidelines"],
    },
    "AU": {
        "regulators": ["AUSTRAC", "ASIC", "APRA"],
        "kyc_level_required": 2,
        "aml_checks": ["austrac", "un_sanctions", "pep"],
        "sar_threshold": 10000,
        "data_retention_years": 7,
        "privacy_law": "Privacy Act (APP)",
        "reporting": ["AUSTRAC SMR", "SUSTR"],
        "crypto_rules": ["AUSTRAC DCE License", "Travel Rule"],
        "insurance_rules": ["Insurance Contracts Act", "APRA Prudential Standards"],
        "restrictions": ["Consumer Data Right (Open Banking)"],
    },
    "SA": {
        "regulators": ["SAMA"],
        "kyc_level_required": 3,
        "aml_checks": ["sama_sanctions", "un_sanctions", "pep"],
        "sar_threshold": 0,
        "data_retention_years": 10,
        "privacy_law": "PDPL",
        "reporting": ["SAMA AML Reporting"],
        "crypto_rules": ["SAMA Crypto Framework"],
        "insurance_rules": ["SAMA Insurance Regs", "Cooperative Insurance Model"],
        "restrictions": ["Sharia compliance", "Anti-Concealment Law"],
    },
    "CH": {
        "regulators": ["FINMA"],
        "kyc_level_required": 2,
        "aml_checks": ["finma_sanctions", "fatf", "pep"],
        "sar_threshold": 0,
        "data_retention_years": 10,
        "privacy_law": "FADP",
        "reporting": ["FINMA Suspicious Activity", "MROS STR"],
        "crypto_rules": ["FINMA DLT Framework", "Travel Rule", "Banking Secrecy"],
        "insurance_rules": ["Insurance Supervision Act", "FINMA Circ-08"],
    },
    "BR": {
        "regulators": ["BACEN", "SUSEP", "CVM"],
        "kyc_level_required": 2,
        "aml_checks": ["bacen_sanctions", "fatf", "pep"],
        "sar_threshold": 0,
        "data_retention_years": 5,
        "privacy_law": "LGPD",
        "reporting": ["COAF Suspicious", "BACEN Reporting"],
        "crypto_rules": ["BACEN Crypto Regulation", "CVM Token Rules"],
        "insurance_rules": ["SUSEP Circular 666", "ANS Health Regs"],
        "restrictions": ["SPI/Pix compliance"],
    },
    "CN": {
        "regulators": ["PBOC", "CBIRC", "CSRC"],
        "kyc_level_required": 3,
        "aml_checks": ["pboc_sanctions", "un_sanctions", "domestic"],
        "sar_threshold": 50000,
        "data_retention_years": 10,
        "privacy_law": "PIPL",
        "reporting": ["PBOC AML Reporting", "SAFE Forex"],
        "crypto_rules": ["Crypto trading ban", "CBDC only"],
        "insurance_rules": ["Insurance Law of China", "CBIRC Capital Regs"],
        "restrictions": ["Capital controls", "Cross-border data approval", "Great Firewall"],
    },
    "ZA": {
        "regulators": ["SARB", "FSCA"],
        "kyc_level_required": 2,
        "aml_checks": ["fica", "un_sanctions", "pep"],
        "sar_threshold": 50000,
        "data_retention_years": 5,
        "privacy_law": "POPIA",
        "reporting": ["FIC STR", "SARB Reporting"],
        "crypto_rules": ["FSCA Crypto Declaration", "Travel Rule"],
        "insurance_rules": ["Insurance Act 18 2017", "COFI Bill"],
    },
    "MX": {
        "regulators": ["CNBV", "CONDUSEF"],
        "kyc_level_required": 2,
        "aml_checks": ["cnbv_sanctions", "fatf", "pep"],
        "sar_threshold": 0,
        "data_retention_years": 7,
        "privacy_law": "LFDPP",
        "reporting": ["CNBV AML Report"],
        "insurance_rules": ["Insurance Circular Única", "CONDUSEF Protection"],
    },
    "CA": {
        "regulators": ["FINTRAC", "OSFI"],
        "kyc_level_required": 2,
        "aml_checks": ["fintrac", "un_sanctions", "pep"],
        "sar_threshold": 10000,
        "data_retention_years": 7,
        "privacy_law": "PIPEDA",
        "reporting": ["FINTRAC STR", "MSB Registration"],
        "crypto_rules": ["FINTRAC MSB for Crypto", "Travel Rule"],
        "insurance_rules": ["OSFI GUID-2019", "CCIR Standards"],
    },
}


class ComplianceRouter:
    def get_country_rules(self, country_code: str) -> dict:
        return COUNTRY_COMPLIANCE.get(country_code.upper(), {})

    def get_all_countries(self) -> dict[str, str]:
        return {code: info.get("regulators", []) for code, info in COUNTRY_COMPLIANCE.items()}

    def check_transaction(self, sender_country: str, recipient_country: str, amount: float, currency: str, asset: str = "fiat") -> dict:
        sender_rules = self.get_country_rules(sender_country)
        recipient_rules = self.get_country_rules(recipient_country)
        checks = []
        requirements = []
        holds = []

        if asset == "crypto":
            crypto_rules = sender_rules.get("crypto_rules", [])
            checks.extend(crypto_rules)
            if "Travel Rule" in str(crypto_rules):
                requirements.append("Travel Rule data sharing (FATF)")

        sar_threshold = sender_rules.get("sar_threshold", 0)
        if amount >= sar_threshold > 0:
            requirements.append(f"Suspicious Activity Report required over {currency} {sar_threshold:,.0f}")
            holds.append("Compliance review for SAR")

        data_retention = sender_rules.get("data_retention_years", 5)
        requirements.append(f"Data retention: {data_retention} years")

        restrictions = sender_rules.get("restrictions", [])
        for r in restrictions:
            checks.append(f"Restriction: {r}")

        is_cross_border = sender_country.upper() != recipient_country.upper()
        if is_cross_border:
            checks.append("Cross-border: additional screening required")
            if recipient_rules.get("privacy_law") != sender_rules.get("privacy_law"):
                requirements.append(f"Cross-border privacy: {sender_rules.get('privacy_law', 'N/A')} -> {recipient_rules.get('privacy_law', 'N/A')}")

        risk_score = self._calculate_risk(amount, is_cross_border, asset, sender_country)
        return {
            "sender_country": sender_country.upper(),
            "recipient_country": recipient_country.upper(),
            "amount": amount,
            "currency": currency,
            "asset": asset,
            "risk_score": risk_score,
            "risk_level": "critical" if risk_score > 75 else "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
            "checks": checks,
            "requirements": requirements,
            "holds": holds,
            "requires_approval": risk_score > 50,
            "sar_required": amount >= sar_threshold,
            "reviewer": "compliance_officer" if risk_score > 50 else "auto_approved",
        }

    def get_required_kyc_level(self, country_code: str, services: list[str]) -> int:
        rules = self.get_country_rules(country_code)
        base_level = rules.get("kyc_level_required", 1)
        if "crypto" in services or "enterprise" in services:
            return max(base_level, 3)
        if "insurance" in services or "swift" in services:
            return max(base_level, 2)
        return base_level

    def get_reporting_obligations(self, country_code: str, transaction: dict) -> list[str]:
        rules = self.get_country_rules(country_code)
        return rules.get("reporting", [])

    def get_compliance_score(self, user_id: str, level: int, country_code: str) -> dict:
        rules = self.get_country_rules(country_code)
        required = rules.get("kyc_level_required", 1)
        score = min(100, (level / required) * 100) if required else 100
        return {
            "user_id": user_id,
            "country": country_code,
            "current_kyc_level": level,
            "required_kyc_level": required,
            "compliance_score": round(score, 2),
            "fully_compliant": level >= required,
            "missing_requirements": [] if level >= required else ["Upgrade KYC level"],
        }

    def _calculate_risk(self, amount: float, is_cross_border: bool, asset: str, country: str) -> int:
        risk = 0
        if amount > 100000:
            risk += 30
        elif amount > 10000:
            risk += 15
        if is_cross_border:
            risk += 20
        if asset == "crypto":
            risk += 15
        if country in ("KP", "IR", "SY", "CU", "MM", "VE"):
            risk += 40
        return min(100, risk)


compliance_router = ComplianceRouter()
