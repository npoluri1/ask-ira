import time
import uuid
from typing import Any

COVERAGE_TYPES = {
    "term_life": {
        "name": "Term Life Insurance",
        "description": "Affordable coverage for a specific period",
        "min_coverage": 100000,
        "max_coverage": 5000000,
        "min_term": 10,
        "max_term": 30,
        "features": ["Convertible to permanent", "Level premiums", "Renewable"],
    },
    "whole_life": {
        "name": "Whole Life Insurance",
        "description": "Lifetime coverage with cash value accumulation",
        "min_coverage": 50000,
        "max_coverage": 2000000,
        "features": ["Cash value growth", "Dividend earning", "Fixed premiums", "Lifetime coverage"],
    },
    "universal_life": {
        "name": "Universal Life Insurance",
        "description": "Flexible premiums with investment component",
        "min_coverage": 100000,
        "max_coverage": 5000000,
        "features": ["Flexible premiums", "Adjustable coverage", "Cash value", "Index-linked options"],
    },
    "health": {
        "name": "Health Insurance",
        "description": "Comprehensive medical coverage",
        "features": ["Hospitalization", "Outpatient care", "Prescription drugs", "Preventive care", "Emergency services"],
        "deductible_options": [500, 1000, 2500, 5000],
        "coinsurance_options": [0.1, 0.2, 0.3],
    },
    "auto": {
        "name": "Auto Insurance",
        "description": "Vehicle protection coverage",
        "features": ["Liability", "Collision", "Comprehensive", "Uninsured motorist", "Roadside assistance"],
        "deductible_options": [250, 500, 1000],
    },
    "homeowners": {
        "name": "Homeowners Insurance",
        "description": "Property and liability protection",
        "features": ["Dwelling coverage", "Personal property", "Liability", "Additional living expenses", "Natural disasters"],
        "deductible_options": [500, 1000, 2500, 5000],
    },
    "renters": {
        "name": "Renters Insurance",
        "description": "Personal property protection for renters",
        "features": ["Personal property", "Liability", "Additional living expenses", "Loss of use"],
        "min_coverage": 10000,
        "max_coverage": 100000,
    },
    "disability": {
        "name": "Disability Insurance",
        "description": "Income protection if unable to work",
        "features": ["Partial disability", "Own occupation", "Residual benefits", "COLA adjustment"],
        "benefit_periods": ["2 years", "5 years", "To age 65", "Lifetime"],
        "waiting_periods": [30, 60, 90, 180, 365],
    },
    "long_term_care": {
        "name": "Long-Term Care Insurance",
        "description": "Coverage for extended care needs",
        "features": ["Nursing home care", "Home health care", "Adult day care", "Alzheimer's coverage", "Inflation protection"],
        "daily_benefit_options": [150, 200, 250, 300, 400],
    },
    "travel": {
        "name": "Travel Insurance",
        "description": "Coverage for travel-related risks",
        "features": ["Trip cancellation", "Medical emergencies", "Lost baggage", "Flight delays", "Emergency evacuation"],
        "max_coverage": 100000,
    },
    "pet": {
        "name": "Pet Insurance",
        "description": "Veterinary care coverage for pets",
        "features": ["Accidents", "Illnesses", "Wellness care", "Dental", "Prescriptions"],
        "deductible_options": [100, 250, 500],
        "reimbursement_options": [0.7, 0.8, 0.9],
    },
}

POLICIES_DB: dict[str, list[dict]] = {}
BENEFICIARIES_DB: dict[str, list[dict]] = {}


class PoliciesEngine:
    def get_coverage_types(self) -> dict:
        return COVERAGE_TYPES

    def get_coverage(self, coverage_id: str) -> dict | None:
        return COVERAGE_TYPES.get(coverage_id)

    def create_policy(self, user_id: str, coverage_type: str, coverage_amount: float, premium: float, term_years: int | None = None, deductibles: dict | None = None) -> dict:
        coverage = COVERAGE_TYPES.get(coverage_type)
        if not coverage:
            raise ValueError(f"Invalid coverage type: {coverage_type}")

        policy = {
            "policy_id": f"POL{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "coverage_type": coverage_type,
            "coverage_name": coverage["name"],
            "coverage_amount": coverage_amount,
            "premium": round(premium, 2),
            "premium_frequency": "monthly",
            "term_years": term_years,
            "deductibles": deductibles or {},
            "status": "active",
            "start_date": time.strftime("%Y-%m-%d", time.gmtime()),
            "end_date": time.strftime("%Y-%m-%d", time.gmtime(time.time() + (term_years or 1) * 365 * 86400)) if term_years else None,
            "features": coverage.get("features", []),
            "cash_value": 0.0 if coverage_type in ("whole_life", "universal_life") else None,
        }

        if user_id not in POLICIES_DB:
            POLICIES_DB[user_id] = []
        POLICIES_DB[user_id].append(policy)
        return policy

    def get_policies(self, user_id: str) -> list[dict]:
        return POLICIES_DB.get(user_id, [])

    def get_policy(self, user_id: str, policy_id: str) -> dict | None:
        for p in POLICIES_DB.get(user_id, []):
            if p["policy_id"] == policy_id:
                return p
        return None

    def cancel_policy(self, user_id: str, policy_id: str) -> dict:
        policy = self.get_policy(user_id, policy_id)
        if not policy:
            raise ValueError("Policy not found")
        policy["status"] = "cancelled"
        policy["cancelled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return policy

    def add_beneficiary(self, user_id: str, policy_id: str, name: str, relationship: str, percentage: float) -> dict:
        beneficiary = {
            "beneficiary_id": f"BEN{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "policy_id": policy_id,
            "name": name,
            "relationship": relationship,
            "percentage": percentage,
        }
        if user_id not in BENEFICIARIES_DB:
            BENEFICIARIES_DB[user_id] = []
        BENEFICIARIES_DB[user_id].append(beneficiary)
        return beneficiary

    def get_beneficiaries(self, user_id: str, policy_id: str) -> list[dict]:
        return [b for b in BENEFICIARIES_DB.get(user_id, []) if b["policy_id"] == policy_id]

    def get_portfolio_summary(self, user_id: str) -> dict:
        policies = self.get_policies(user_id)
        total_coverage = sum(p["coverage_amount"] for p in policies if p["status"] == "active")
        total_premium = sum(p["premium"] for p in policies if p["status"] == "active")
        by_type: dict[str, Any] = {}
        for p in policies:
            t = p["coverage_type"]
            if t not in by_type:
                by_type[t] = {"count": 0, "total_coverage": 0}
            by_type[t]["count"] += 1
            if p["status"] == "active":
                by_type[t]["total_coverage"] += p["coverage_amount"]
        return {
            "user_id": user_id,
            "active_policies": sum(1 for p in policies if p["status"] == "active"),
            "total_coverage": round(total_coverage, 2),
            "total_monthly_premium": round(total_premium, 2),
            "annual_premium": round(total_premium * 12, 2),
            "breakdown_by_type": by_type,
        }

    def create_demo_data(self, user_id: str):
        self.create_policy(user_id, "term_life", 500000, 45.00, term_years=20)
        self.create_policy(user_id, "health", 1000000, 350.00, deductibles={"individual": 1500, "family": 3000})
        self.create_policy(user_id, "auto", 50000, 120.00, deductibles={"collision": 500, "comprehensive": 250})
        self.create_policy(user_id, "travel", 50000, 25.00)

        self.add_beneficiary(user_id, POLICIES_DB[user_id][0]["policy_id"], "Jane Doe", "Spouse", 100)
