import time
import uuid
from typing import Any

LOAN_TYPES = {
    "personal": {"name": "Personal Loan", "min_amount": 1000, "max_amount": 50000, "base_rate": 0.0899, "min_term": 12, "max_term": 60},
    "auto": {"name": "Auto Loan", "min_amount": 5000, "max_amount": 100000, "base_rate": 0.0699, "min_term": 24, "max_term": 72},
    "mortgage": {"name": "Mortgage", "min_amount": 50000, "max_amount": 2000000, "base_rate": 0.0649, "min_term": 120, "max_term": 360},
    "student": {"name": "Student Loan", "min_amount": 1000, "max_amount": 100000, "base_rate": 0.0499, "min_term": 60, "max_term": 240},
    "home_equity": {"name": "Home Equity Loan", "min_amount": 10000, "max_amount": 500000, "base_rate": 0.0749, "min_term": 60, "max_term": 180},
    "business": {"name": "Business Loan", "min_amount": 10000, "max_amount": 500000, "base_rate": 0.0999, "min_term": 12, "max_term": 84},
}

LOANS_DB: dict[str, list[dict]] = {}


class LoansEngine:
    def get_loan_products(self) -> dict:
        return LOAN_TYPES

    def get_loan_details(self, loan_type: str) -> dict | None:
        return LOAN_TYPES.get(loan_type)

    def calculate_emi(self, principal: float, annual_rate: float, term_months: int) -> dict:
        monthly_rate = annual_rate / 12
        emi = principal * monthly_rate * (1 + monthly_rate) ** term_months / ((1 + monthly_rate) ** term_months - 1)
        total_payment = emi * term_months
        total_interest = total_payment - principal
        return {
            "principal": round(principal, 2),
            "annual_rate": round(annual_rate * 100, 2),
            "monthly_rate": round(monthly_rate * 100, 4),
            "term_months": term_months,
            "emi": round(emi, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "amortization_schedule": self._generate_amortization(principal, annual_rate, term_months),
        }

    def apply_loan(self, user_id: str, loan_type: str, amount: float, term_months: int) -> dict:
        product = LOAN_TYPES.get(loan_type)
        if not product:
            raise ValueError(f"Invalid loan type: {loan_type}")
        if amount < product["min_amount"] or amount > product["max_amount"]:
            raise ValueError(f"Amount must be between ${product['min_amount']:,} and ${product['max_amount']:,}")
        if term_months < product["min_term"] or term_months > product["max_term"]:
            raise ValueError(f"Term must be between {product['min_term']} and {product['max_term']} months")

        rate = self._calculate_risk_adjusted_rate(loan_type, amount, user_id)
        emi_calc = self.calculate_emi(amount, rate, term_months)

        loan = {
            "loan_id": f"LN{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "loan_type": loan_type,
            "product_name": product["name"],
            "principal": round(amount, 2),
            "annual_rate": round(rate * 100, 2),
            "term_months": term_months,
            "emi": emi_calc["emi"],
            "total_payment": emi_calc["total_payment"],
            "total_interest": emi_calc["total_interest"],
            "status": "approved",
            "disbursed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "next_payment_date": time.strftime("%Y-%m-%d", time.gmtime(time.time() + 30 * 86400)),
            "remaining_balance": round(amount, 2),
            "payments_made": 0,
            "remaining_terms": term_months,
        }

        if user_id not in LOANS_DB:
            LOANS_DB[user_id] = []
        LOANS_DB[user_id].append(loan)
        return loan

    def get_loans(self, user_id: str) -> list[dict]:
        return LOANS_DB.get(user_id, [])

    def make_payment(self, user_id: str, loan_id: str) -> dict:
        for loan in LOANS_DB.get(user_id, []):
            if loan["loan_id"] == loan_id:
                if loan["remaining_balance"] <= 0:
                    raise ValueError("Loan is already fully paid")
                payment = min(loan["emi"], loan["remaining_balance"])
                loan["remaining_balance"] = round(loan["remaining_balance"] - payment, 2)
                loan["payments_made"] += 1
                loan["remaining_terms"] -= 1
                if loan["remaining_balance"] <= 0:
                    loan["status"] = "paid"
                return {"loan_id": loan_id, "payment": payment, "remaining_balance": loan["remaining_balance"], "status": loan["status"]}
        raise ValueError("Loan not found")

    def get_loan_summary(self, user_id: str) -> dict:
        loans = self.get_loans(user_id)
        total_principal = sum(l["principal"] for l in loans)
        total_remaining = sum(l["remaining_balance"] for l in loans)
        total_emi = sum(l["emi"] for l in loans)
        return {
            "user_id": user_id,
            "active_loans": sum(1 for l in loans if l["status"] == "approved"),
            "paid_loans": sum(1 for l in loans if l["status"] == "paid"),
            "total_principal": round(total_principal, 2),
            "total_remaining": round(total_remaining, 2),
            "total_monthly_emi": round(total_emi, 2),
            "total_paid_percent": round((total_principal - total_remaining) / total_principal * 100, 2) if total_principal else 0,
        }

    def create_demo_data(self, user_id: str):
        self.apply_loan(user_id, "personal", 15000, 36)
        self.apply_loan(user_id, "auto", 35000, 60)

    def _calculate_risk_adjusted_rate(self, loan_type: str, amount: float, user_id: str) -> float:
        base_rate = LOAN_TYPES[loan_type]["base_rate"]
        risk_adjustment = 0
        existing = len(LOANS_DB.get(user_id, []))
        if existing > 2:
            risk_adjustment += 0.005
        if amount > 100000:
            risk_adjustment += 0.01
        return base_rate + risk_adjustment

    def _generate_amortization(self, principal: float, annual_rate: float, term_months: int) -> list[dict]:
        monthly_rate = annual_rate / 12
        emi = principal * monthly_rate * (1 + monthly_rate) ** term_months / ((1 + monthly_rate) ** term_months - 1)
        schedule = []
        balance = principal
        for month in range(1, min(term_months + 1, 13)):
            interest = balance * monthly_rate
            principal_paid = emi - interest
            balance -= principal_paid
            schedule.append({
                "month": month,
                "emi": round(emi, 2),
                "interest": round(interest, 2),
                "principal_paid": round(principal_paid, 2),
                "balance": round(max(balance, 0), 2),
            })
        return schedule
