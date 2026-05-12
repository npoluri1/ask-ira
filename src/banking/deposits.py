import time
import uuid
from typing import Any

DEPOSIT_PRODUCTS = {
    "savings": {
        "name": "High-Yield Savings Account",
        "min_deposit": 0,
        "interest_rate": 0.045,
        "compound_frequency": "daily",
        "liquidity": "immediate",
        "fdic_insured": True,
    },
    "cd_6m": {
        "name": "6-Month CD",
        "min_deposit": 1000,
        "interest_rate": 0.052,
        "compound_frequency": "maturity",
        "term_days": 180,
        "early_withdrawal_penalty": "3 months interest",
        "fdic_insured": True,
    },
    "cd_12m": {
        "name": "12-Month CD",
        "min_deposit": 1000,
        "interest_rate": 0.055,
        "compound_frequency": "maturity",
        "term_days": 365,
        "early_withdrawal_penalty": "3 months interest",
        "fdic_insured": True,
    },
    "cd_24m": {
        "name": "24-Month CD",
        "min_deposit": 1000,
        "interest_rate": 0.058,
        "compound_frequency": "maturity",
        "term_days": 730,
        "early_withdrawal_penalty": "6 months interest",
        "fdic_insured": True,
    },
    "money_market": {
        "name": "Money Market Account",
        "min_deposit": 2500,
        "interest_rate": 0.052,
        "compound_frequency": "monthly",
        "liquidity": "limited (6 withdrawals/month)",
        "fdic_insured": True,
    },
    "ira_cd": {
        "name": "IRA CD",
        "min_deposit": 500,
        "interest_rate": 0.056,
        "compound_frequency": "maturity",
        "term_days": 365,
        "early_withdrawal_penalty": "6 months interest + IRS penalty",
        "tax_advantaged": True,
        "fdic_insured": True,
    },
    "fixed_deposit": {
        "name": "Fixed Deposit",
        "min_deposit": 5000,
        "interest_rate": 0.065,
        "compound_frequency": "quarterly",
        "term_days": 365,
        "early_withdrawal_penalty": "1% of principal",
        "loan_eligible": True,
    },
    "recurring_deposit": {
        "name": "Recurring Deposit",
        "min_monthly": 500,
        "max_monthly": 100000,
        "interest_rate": 0.06,
        "compound_frequency": "quarterly",
        "min_term_months": 6,
        "max_term_months": 120,
    },
}

DEPOSITS_DB: dict[str, list[dict]] = {}


class DepositsEngine:
    def get_products(self) -> dict:
        return DEPOSIT_PRODUCTS

    def open_deposit(self, user_id: str, product_id: str, amount: float, **kwargs) -> dict:
        product = DEPOSIT_PRODUCTS.get(product_id)
        if not product:
            raise ValueError(f"Invalid product: {product_id}")
        if amount < product.get("min_deposit", 0):
            raise ValueError(f"Minimum deposit is ${product['min_deposit']:,}")

        now = time.time()
        deposit = {
            "deposit_id": f"DEP{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "product_id": product_id,
            "product_name": product["name"],
            "amount": round(amount, 2),
            "interest_rate": product["interest_rate"],
            "status": "active",
            "opened_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "matures_at": None,
        }

        if "term_days" in product:
            deposit["matures_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + product["term_days"] * 86400))
            deposit["early_withdrawal_penalty"] = product.get("early_withdrawal_penalty", "None")
            deposit["auto_renew"] = kwargs.get("auto_renew", True)

        if product_id == "recurring_deposit":
            deposit["monthly_amount"] = amount
            deposit["term_months"] = kwargs.get("term_months", 12)
            deposit["total_expected"] = round(amount * deposit["term_months"], 2)

        if user_id not in DEPOSITS_DB:
            DEPOSITS_DB[user_id] = []
        DEPOSITS_DB[user_id].append(deposit)
        return deposit

    def get_deposits(self, user_id: str) -> list[dict]:
        return DEPOSITS_DB.get(user_id, [])

    def get_matured_value(self, deposit_id: str, user_id: str) -> dict:
        for d in DEPOSITS_DB.get(user_id, []):
            if d["deposit_id"] == deposit_id:
                rate = d["interest_rate"]
                amount = d["amount"]
                from datetime import datetime
                opened = datetime.strptime(d["opened_at"], "%Y-%m-%dT%H:%M:%SZ")
                now_dt = datetime.utcnow()
                days = (now_dt - opened).days
                if d.get("matures_at"):
                    maturity = datetime.strptime(d["matures_at"], "%Y-%m-%dT%H:%M:%SZ")
                    days = (maturity - opened).days
                matured = amount * (1 + rate * days / 365)
                return {
                    "deposit_id": deposit_id,
                    "initial_amount": amount,
                    "interest_rate": rate,
                    "days_held": max(days, 0),
                    "matured_value": round(matured, 2),
                    "interest_earned": round(matured - amount, 2),
                }
        raise ValueError("Deposit not found")

    def close_deposit(self, user_id: str, deposit_id: str) -> dict:
        for d in DEPOSITS_DB.get(user_id, []):
            if d["deposit_id"] == deposit_id:
                d["status"] = "closed"
                d["closed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                return d
        raise ValueError("Deposit not found")

    def create_demo_data(self, user_id: str):
        self.open_deposit(user_id, "cd_12m", 10000, auto_renew=True)
        self.open_deposit(user_id, "money_market", 25000)
        self.open_deposit(user_id, "fixed_deposit", 50000, auto_renew=False)
