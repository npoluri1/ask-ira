import time
import uuid
from typing import Any

FD_PRODUCTS = {
    "fd_3m": {"name": "3 Month Fixed Deposit", "min_amount": 5000, "max_amount": 10000000, "interest_rate": 0.055, "term_days": 90, "compound": "maturity"},
    "fd_6m": {"name": "6 Month Fixed Deposit", "min_amount": 5000, "max_amount": 10000000, "interest_rate": 0.060, "term_days": 180, "compound": "maturity"},
    "fd_1y": {"name": "1 Year Fixed Deposit", "min_amount": 5000, "max_amount": 10000000, "interest_rate": 0.065, "term_days": 365, "compound": "quarterly"},
    "fd_2y": {"name": "2 Year Fixed Deposit", "min_amount": 5000, "max_amount": 5000000, "interest_rate": 0.068, "term_days": 730, "compound": "quarterly"},
    "fd_3y": {"name": "3 Year Fixed Deposit", "min_amount": 5000, "max_amount": 5000000, "interest_rate": 0.070, "term_days": 1095, "compound": "quarterly"},
    "fd_5y": {"name": "5 Year Fixed Deposit", "min_amount": 5000, "max_amount": 5000000, "interest_rate": 0.075, "term_days": 1825, "compound": "yearly"},
    "tax_saver_fd": {"name": "Tax Saver FD (5 Year Lock-in)", "min_amount": 1000, "max_amount": 150000, "interest_rate": 0.070, "term_days": 1825, "compound": "yearly", "tax_benefit": "Section 80C"},
    "senior_citizen_fd": {"name": "Senior Citizen FD", "min_amount": 5000, "max_amount": 10000000, "interest_rate": 0.075, "term_days": 365, "compound": "quarterly", "extra_rate": 0.005},
    "recurring_deposit": {"name": "Recurring Deposit", "min_monthly": 500, "max_monthly": 100000, "interest_rate": 0.060, "compound": "quarterly", "min_term_months": 6, "max_term_months": 120},
    "cumulative_fd": {"name": "Cumulative Fixed Deposit", "min_amount": 10000, "max_amount": 50000000, "interest_rate": 0.068, "term_days": 365, "compound": "quarterly", "interest_payout": "at maturity"},
    "non_cumulative_fd": {"name": "Non-Cumulative Fixed Deposit", "min_amount": 10000, "max_amount": 50000000, "interest_rate": 0.060, "term_days": 365, "compound": "quarterly", "interest_payout": "monthly/quarterly"},
}

FD_HOLDINGS_DB: dict[str, list[dict]] = {}


class FixedDepositsEngine:
    def get_products(self) -> dict:
        return FD_PRODUCTS

    def get_product(self, product_id: str) -> dict | None:
        return FD_PRODUCTS.get(product_id)

    def calculate_maturity(self, product_id: str, amount: float, term_days: int | None = None) -> dict:
        product = FD_PRODUCTS.get(product_id)
        if not product:
            raise ValueError(f"Invalid product: {product_id}")
        rate = product["interest_rate"]
        days = term_days or product.get("term_days", 365)
        years = days / 365

        if product.get("compound") == "quarterly":
            maturity = amount * (1 + rate / 4) ** (4 * years)
        elif product.get("compound") == "yearly":
            maturity = amount * (1 + rate) ** years
        else:
            maturity = amount * (1 + rate * years)

        interest_earned = maturity - amount
        return {
            "product": product["name"],
            "principal": round(amount, 2),
            "interest_rate": rate,
            "term_days": days,
            "maturity_amount": round(maturity, 2),
            "interest_earned": round(interest_earned, 2),
            "effective_yield": round((maturity / amount - 1) * 100, 2),
        }

    def open_fd(self, user_id: str, product_id: str, amount: float) -> dict:
        product = FD_PRODUCTS.get(product_id)
        if not product:
            raise ValueError(f"Invalid product: {product_id}")
        if amount < product.get("min_amount", 0):
            raise ValueError(f"Minimum amount is ${product['min_amount']:,}")

        calc = self.calculate_maturity(product_id, amount)
        now = time.time()
        deposit = {
            "fd_id": f"FD{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "product_id": product_id,
            "product_name": product["name"],
            "principal": round(amount, 2),
            "interest_rate": product["interest_rate"],
            "maturity_amount": calc["maturity_amount"],
            "term_days": product.get("term_days", 365),
            "status": "active",
            "opened_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "matures_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + product.get("term_days", 365) * 86400)),
            "interest_payout": product.get("interest_payout", "at maturity"),
            "loan_eligible": True,
            "auto_renew": True,
        }

        if user_id not in FD_HOLDINGS_DB:
            FD_HOLDINGS_DB[user_id] = []
        FD_HOLDINGS_DB[user_id].append(deposit)
        return deposit

    def get_holdings(self, user_id: str) -> list[dict]:
        return FD_HOLDINGS_DB.get(user_id, [])

    def close_fd(self, user_id: str, fd_id: str) -> dict:
        for fd in FD_HOLDINGS_DB.get(user_id, []):
            if fd["fd_id"] == fd_id:
                fd["status"] = "closed"
                fd["closed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                return fd
        raise ValueError("FD not found")

    def get_portfolio_summary(self, user_id: str) -> dict:
        holdings = self.get_holdings(user_id)
        total_principal = sum(h["principal"] for h in holdings if h["status"] == "active")
        total_maturity = sum(h["maturity_amount"] for h in holdings if h["status"] == "active")
        return {
            "user_id": user_id,
            "active_deposits": sum(1 for h in holdings if h["status"] == "active"),
            "total_principal": round(total_principal, 2),
            "total_maturity_value": round(total_maturity, 2),
            "total_interest": round(total_maturity - total_principal, 2),
        }

    def create_demo_data(self, user_id: str):
        self.open_fd(user_id, "fd_1y", 50000)
        self.open_fd(user_id, "fd_3y", 100000)
        self.open_fd(user_id, "tax_saver_fd", 150000)
