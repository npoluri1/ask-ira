import time
import uuid
from typing import Any

REPORTS_DB: dict[str, list[dict]] = {}

REPORTING_THRESHOLDS: dict[str, dict[str, float]] = {
    "US": {"ctr": 10000, "sar": 5000, "fbar": 10000, "fatca": 50000, "cpt": 100000},
    "UK": {"ctr": 10000, "sar": 5000, "fbar": 10000, "fatca": 50000, "cpt": 100000},
    "EU": {"ctr": 10000, "sar": 10000, "fbar": 10000, "fatca": 50000, "cpt": 100000},
    "AE": {"ctr": 55000, "sar": 55000, "fbar": 10000, "fatca": 50000, "cpt": 350000},
    "SG": {"ctr": 20000, "sar": 20000, "fbar": 10000, "fatca": 50000, "cpt": 200000},
    "CH": {"ctr": 15000, "sar": 15000, "fbar": 10000, "fatca": 50000, "cpt": 100000},
    "HK": {"ctr": 12000, "sar": 12000, "fbar": 10000, "fatca": 50000, "cpt": 80000},
    "IN": {"ctr": 10000, "sar": 50000, "fbar": 10000, "fatca": 50000, "cpt": 200000},
}


class ReportingEngine:
    def _store_report(self, user_id: str, report: dict[str, Any]) -> dict[str, Any]:
        if user_id not in REPORTS_DB:
            REPORTS_DB[user_id] = []
        REPORTS_DB[user_id].append(report)
        return report

    def generate_sar_report(self, data: dict[str, Any]) -> dict[str, Any]:
        report = {
            "report_id": f"SAR-{uuid.uuid4().hex[:8].upper()}",
            "report_type": "Suspicious Activity Report",
            "regulatory_body": data.get("regulatory_body", "FinCEN"),
            "filing_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "subject": {
                "name": data.get("subject_name", ""),
                "user_id": data.get("user_id", ""),
                "account_number": data.get("account_number", ""),
            },
            "transaction_details": {
                "amount": data.get("amount", 0),
                "currency": data.get("currency", "USD"),
                "counterparty": data.get("counterparty", ""),
                "date": data.get("transaction_date", ""),
                "channel": data.get("channel", "online"),
            },
            "suspicion_reason": data.get("reason", ""),
            "narrative": data.get("narrative", ""),
            "supporting_evidence": data.get("evidence", []),
            "filed_by": data.get("filing_officer", "Compliance Officer"),
            "status": "submitted",
            "submission_channel": "electronic",
        }
        return self._store_report(data.get("user_id", ""), report)

    def generate_ctr_report(self, data: dict[str, Any]) -> dict[str, Any]:
        report = {
            "report_id": f"CTR-{uuid.uuid4().hex[:8].upper()}",
            "report_type": "Currency Transaction Report",
            "regulatory_body": data.get("regulatory_body", "FinCEN"),
            "filing_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "filer": {
                "name": data.get("filer_name", ""),
                "ein": data.get("filer_ein", ""),
            },
            "subject": {
                "name": data.get("subject_name", ""),
                "user_id": data.get("user_id", ""),
                "account_number": data.get("account_number", ""),
                "tax_id": data.get("tax_id", ""),
            },
            "transaction": {
                "amount": data.get("amount", 0),
                "currency": data.get("currency", "USD"),
                "type": data.get("transaction_type", "withdrawal"),
                "method": data.get("payment_method", "wire"),
                "date": data.get("transaction_date", ""),
                "location": data.get("location", ""),
            },
            "multiple_transactions": data.get("multiple_transactions", False),
            "status": "submitted",
        }
        return self._store_report(data.get("user_id", ""), report)

    def generate_fbar_report(self, data: dict[str, Any]) -> dict[str, Any]:
        report = {
            "report_id": f"FBAR-{uuid.uuid4().hex[:8].upper()}",
            "report_type": "Foreign Bank Account Report",
            "filing_year": data.get("filing_year", time.strftime("%Y")),
            "filing_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "filer": {
                "name": data.get("filer_name", ""),
                "tax_id": data.get("tax_id", ""),
                "address": data.get("address", ""),
            },
            "accounts": data.get("accounts", []),
            "total_value": data.get("total_value", 0),
            "currency": data.get("currency", "USD"),
            "certified": False,
            "status": "draft",
        }
        return self._store_report(data.get("user_id", ""), report)

    def generate_fatca_report(self, data: dict[str, Any]) -> dict[str, Any]:
        report = {
            "report_id": f"FATCA-{uuid.uuid4().hex[:8].upper()}",
            "report_type": "FATCA Report",
            "filing_year": data.get("filing_year", time.strftime("%Y")),
            "filing_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "financial_institution": data.get("institution_name", ""),
            "giin": data.get("giin", ""),
            "account_holder": {
                "name": data.get("account_holder_name", ""),
                "tax_residency_country": data.get("tax_country", "US"),
                "tax_id": data.get("tax_id", ""),
                "dob": data.get("date_of_birth", ""),
            },
            "account": {
                "number": data.get("account_number", ""),
                "balance": data.get("account_balance", 0),
                "currency": data.get("currency", "USD"),
                "type": data.get("account_type", "deposit"),
            },
            "us_indicia": data.get("us_indicia", []),
            "status": "draft",
        }
        return self._store_report(data.get("user_id", ""), report)

    def generate_tax_report(self, user_id: str, year: int) -> dict[str, Any]:
        report = {
            "report_id": f"TAX-{uuid.uuid4().hex[:8].upper()}",
            "report_type": "Tax Report",
            "user_id": user_id,
            "tax_year": year,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "income": {
                "capital_gains": {
                    "short_term": {"realized": 0, "unrealized": 0},
                    "long_term": {"realized": 0, "unrealized": 0},
                    "total_realized": 0,
                },
                "dividends": {
                    "qualified": 0,
                    "ordinary": 0,
                    "total": 0,
                },
                "interest": {
                    "taxable": 0,
                    "tax_exempt": 0,
                    "total": 0,
                },
            },
            "deductions": {
                "trading_fees": 0,
                "advisory_fees": 0,
                "total": 0,
            },
            "wash_sales": [],
            "tax_owed_estimate": 0,
            "status": "preliminary",
        }
        return self._store_report(user_id, report)

    def get_reporting_thresholds(self) -> dict[str, dict[str, float]]:
        return {k: dict(v) for k, v in REPORTING_THRESHOLDS.items()}

    def get_reports(self, user_id: str) -> list[dict[str, Any]]:
        return REPORTS_DB.get(user_id, [])

    def create_demo_data(self, user_id: str):
        if REPORTS_DB.get(user_id):
            return
        self.generate_sar_report({
            "user_id": user_id,
            "subject_name": "John Doe",
            "amount": 25000,
            "currency": "USD",
            "counterparty": "Offshore Trading Ltd",
            "transaction_date": "2024-03-15",
            "reason": "Unusual pattern of near-threshold transactions",
            "narrative": "Subject conducted multiple transactions just below reporting threshold over 3-day period. Pattern consistent with structuring.",
            "evidence": ["Transaction logs showing 5 transactions of $9,800 each"],
            "regulatory_body": "FinCEN",
        })
        self.generate_ctr_report({
            "user_id": user_id,
            "subject_name": "John Doe",
            "amount": 15000,
            "filer_name": "IRA Banking Corp",
            "filer_ein": "XX-XXXXXXX",
            "account_number": "IRA-1001",
            "transaction_type": "deposit",
            "payment_method": "cash",
            "transaction_date": "2024-03-20",
            "location": "New York, NY",
            "regulatory_body": "FinCEN",
        })
