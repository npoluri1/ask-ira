import time
import uuid
from typing import Any

INSURANCE_WALLETS_DB: dict[str, list[dict]] = {}

POLICY_TYPES: list[str] = [
    "term_life", "whole_life", "universal_life", "variable_life",
    "ulip", "critical_illness", "disability", "long_term_care",
    "health_insurance", "accident", "travel_insurance",
]

COVERAGE_CATEGORIES: list[str] = [
    "life", "health", "disability", "property", "liability", "travel", "investment",
]


class InsuranceWalletEngine:
    def create_insurance_wallet(self, user_id: str, wallet_name: str = "") -> dict[str, Any]:
        wallet: dict[str, Any] = {
            "wallet_id": f"INS-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "wallet_name": wallet_name or "Insurance Portfolio",
            "policies": [],
            "total_premiums_paid": 0.0,
            "pending_claims": 0,
            "approved_payouts": 0.0,
            "cash_value": 0.0,
            "investment_value": 0.0,
            "total_coverage_active": 0.0,
            "status": "active",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if user_id not in INSURANCE_WALLETS_DB:
            INSURANCE_WALLETS_DB[user_id] = []
        INSURANCE_WALLETS_DB[user_id].append(wallet)
        return wallet

    def get_wallets(self, user_id: str) -> list[dict[str, Any]]:
        return INSURANCE_WALLETS_DB.get(user_id, [])

    def get_wallet(self, user_id: str, wallet_id: str) -> dict[str, Any] | None:
        for w in INSURANCE_WALLETS_DB.get(user_id, []):
            if w["wallet_id"] == wallet_id:
                return w
        return None

    def _add_policy(self, user_id: str, wallet_id: str, policy: dict[str, Any]) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Insurance wallet not found")

        policy["policy_id"] = f"POL-{uuid.uuid4().hex[:8].upper()}"
        policy["added_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        wallet["policies"].append(policy)

        wallet["total_premiums_paid"] = round(
            wallet["total_premiums_paid"] + policy.get("annual_premium", 0), 2
        )
        wallet["total_coverage_active"] = round(
            wallet["total_coverage_active"] + policy.get("coverage_amount", 0), 2
        )
        coverage_type = policy.get("coverage_type", "life")
        if coverage_type in ("whole_life", "universal_life", "variable_life"):
            wallet["cash_value"] = round(
                wallet["cash_value"] + policy.get("cash_value", 0), 2
            )
        if coverage_type == "ulip":
            wallet["investment_value"] = round(
                wallet["investment_value"] + policy.get("investment_value", 0), 2
            )

        return policy

    def track_premiums(self, user_id: str, wallet_id: str) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Insurance wallet not found")

        now = time.time()
        schedule: list[dict[str, Any]] = []
        for policy in wallet["policies"]:
            premium = policy.get("annual_premium", 0)
            next_due_ts = now + 30 * 86400
            schedule.append({
                "policy_id": policy["policy_id"],
                "policy_name": policy.get("policy_name", ""),
                "annual_premium": premium,
                "frequency": policy.get("payment_frequency", "annual"),
                "next_due": time.strftime("%Y-%m-%d", time.gmtime(next_due_ts)),
                "status": "upcoming",
            })

        return {
            "wallet_id": wallet_id,
            "total_annual_premiums": round(wallet["total_premiums_paid"], 2),
            "upcoming_payments": [s for s in schedule if s["status"] == "upcoming"],
            "overdue_payments": [],
            "paid_history": [
                {
                    "policy_id": p["policy_id"],
                    "policy_name": p.get("policy_name", ""),
                    "amount": p.get("annual_premium", 0),
                    "paid_date": p.get("added_at", ""),
                    "method": "automatic",
                }
                for p in wallet["policies"]
            ],
        }

    def track_claims(self, user_id: str, wallet_id: str) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Insurance wallet not found")

        claims: list[dict[str, Any]] = []
        for policy in wallet["policies"]:
            for claim in policy.get("claims", []):
                claims.append(claim)

        pending = [c for c in claims if c.get("status") == "pending"]
        approved = [c for c in claims if c.get("status") == "approved"]
        rejected = [c for c in claims if c.get("status") == "rejected"]

        return {
            "wallet_id": wallet_id,
            "total_claims": len(claims),
            "pending_claims": len(pending),
            "approved_claims": len(approved),
            "rejected_claims": len(rejected),
            "total_payout": round(wallet["approved_payouts"], 2),
            "claims": claims,
            "average_processing_days": 14,
        }

    def get_cash_value(self, user_id: str, wallet_id: str) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Insurance wallet not found")

        policies_with_cash = [
            p for p in wallet["policies"]
            if p.get("coverage_type") in ("whole_life", "universal_life", "variable_life")
        ]

        return {
            "wallet_id": wallet_id,
            "total_cash_value": round(wallet["cash_value"], 2),
            "policies": [
                {
                    "policy_id": p["policy_id"],
                    "policy_name": p.get("policy_name", ""),
                    "cash_value": p.get("cash_value", 0),
                    "surrender_value": round(p.get("cash_value", 0) * 0.85, 2),
                    "loan_available": round(p.get("cash_value", 0) * 0.9, 2),
                }
                for p in policies_with_cash
            ],
            "last_valuation": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def get_policy_coverage_summary(self, user_id: str, wallet_id: str) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Insurance wallet not found")

        by_type: dict[str, dict[str, Any]] = {}
        for p in wallet["policies"]:
            ctype = p.get("coverage_type", "other")
            if ctype not in by_type:
                by_type[ctype] = {"count": 0, "total_coverage": 0.0, "total_premium": 0.0}
            by_type[ctype]["count"] += 1
            by_type[ctype]["total_coverage"] += p.get("coverage_amount", 0)
            by_type[ctype]["total_premium"] += p.get("annual_premium", 0)

        return {
            "wallet_id": wallet_id,
            "total_coverage": round(wallet["total_coverage_active"], 2),
            "total_premiums": round(wallet["total_premiums_paid"], 2),
            "coverage_by_type": {k: {sk: round(sv, 2) if isinstance(sv, float) else sv for sk, sv in v.items()} for k, v in by_type.items()},
            "coverage_to_premium_ratio": round(
                wallet["total_coverage_active"] / wallet["total_premiums_paid"], 2
            ) if wallet["total_premiums_paid"] else 0,
        }

    def create_demo_data(self, user_id: str):
        if INSURANCE_WALLETS_DB.get(user_id):
            return
        wallet = self.create_insurance_wallet(user_id, "Life & Health Portfolio")

        self._add_policy(user_id, wallet["wallet_id"], {
            "policy_name": "Term Life - 20 Year",
            "coverage_type": "term_life",
            "coverage_amount": 500000,
            "annual_premium": 1200,
            "payment_frequency": "annual",
            "term_years": 20,
            "start_date": "2024-01-01",
            "end_date": "2044-01-01",
            "beneficiaries": ["Jane Doe"],
            "cash_value": 0,
            "claims": [],
            "status": "active",
        })

        self._add_policy(user_id, wallet["wallet_id"], {
            "policy_name": "Whole Life - Retirement",
            "coverage_type": "whole_life",
            "coverage_amount": 250000,
            "annual_premium": 3500,
            "payment_frequency": "annual",
            "start_date": "2022-06-15",
            "cash_value": 18000,
            "claims": [],
            "status": "active",
        })

        self._add_policy(user_id, wallet["wallet_id"], {
            "policy_name": "Critical Illness Cover",
            "coverage_type": "critical_illness",
            "coverage_amount": 100000,
            "annual_premium": 800,
            "payment_frequency": "annual",
            "start_date": "2023-03-01",
            "cash_value": 0,
            "claims": [
                {
                    "claim_id": f"CLM-{uuid.uuid4().hex[:8].upper()}",
                    "type": "critical_illness",
                    "amount": 50000,
                    "status": "approved",
                    "filed_date": "2024-02-10",
                    "approved_date": "2024-03-05",
                    "payout": 50000,
                }
            ],
            "status": "active",
        })
        wallet["approved_payouts"] = 50000
        wallet["pending_claims"] = 0

        self._add_policy(user_id, wallet["wallet_id"], {
            "policy_name": "ULIP - Growth Plus",
            "coverage_type": "ulip",
            "coverage_amount": 150000,
            "annual_premium": 5000,
            "payment_frequency": "annual",
            "start_date": "2023-09-01",
            "cash_value": 0,
            "investment_value": 22000,
            "fund_allocation": {"equity": 60, "debt": 30, "money_market": 10},
            "claims": [],
            "status": "active",
        })
        wallet["investment_value"] = 22000
