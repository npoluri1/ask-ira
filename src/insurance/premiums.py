import math
import time
import uuid

PREMIUM_HISTORY_DB: dict[str, list[dict]] = {}


class PremiumsEngine:
    def calculate_premium(self, coverage_type: str, coverage_amount: float, age: int = 35, smoker: bool = False, health_rating: str = "standard", term_years: int = 20, vehicle_value: float | None = None, property_value: float | None = None) -> dict:
        base_rate = self._get_base_rate(coverage_type, coverage_amount)

        age_factor = self._age_factor(age)
        health_factor = {"preferred": 0.85, "standard": 1.0, "substandard": 1.5, "smoker": 2.0}.get(health_rating, 1.0)
        if smoker:
            health_factor = 2.0

        monthly_premium = base_rate * age_factor * health_factor
        annual_premium = monthly_premium * 12

        breakdown = {
            "base_rate": round(base_rate, 2),
            "age_factor": age_factor,
            "health_factor": health_factor,
            "monthly_premium": round(monthly_premium, 2),
            "annual_premium": round(annual_premium, 2),
        }

        if coverage_type == "auto" and vehicle_value:
            vehicle_factor = vehicle_value / 50000
            monthly_premium *= vehicle_factor
            breakdown["vehicle_factor"] = round(vehicle_factor, 2)

        if coverage_type in ("homeowners", "renters") and property_value:
            property_factor = math.sqrt(property_value / 250000)
            monthly_premium *= property_factor
            breakdown["property_factor"] = round(property_factor, 2)

        monthly_premium = round(monthly_premium, 2)

        return {
            "coverage_type": coverage_type,
            "coverage_amount": coverage_amount,
            "monthly_premium": monthly_premium,
            "annual_premium": round(monthly_premium * 12, 2),
            "breakdown": breakdown,
        }

    def record_payment(self, user_id: str, policy_id: str, amount: float, payment_method: str = "auto_debit") -> dict:
        payment = {
            "payment_id": f"PRM{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "policy_id": policy_id,
            "amount": round(amount, 2),
            "payment_method": payment_method,
            "status": "completed",
            "paid_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "period_start": time.strftime("%Y-%m-%d", time.gmtime()),
            "period_end": time.strftime("%Y-%m-%d", time.gmtime(time.time() + 30 * 86400)),
        }

        if user_id not in PREMIUM_HISTORY_DB:
            PREMIUM_HISTORY_DB[user_id] = []
        PREMIUM_HISTORY_DB[user_id].append(payment)
        return payment

    def get_payment_history(self, user_id: str, policy_id: str | None = None) -> list[dict]:
        payments = PREMIUM_HISTORY_DB.get(user_id, [])
        if policy_id:
            payments = [p for p in payments if p["policy_id"] == policy_id]
        return list(reversed(payments))

    def estimate_lifetime_premium(self, monthly_premium: float, term_years: int) -> dict:
        total = monthly_premium * 12 * term_years
        return {
            "monthly_premium": round(monthly_premium, 2),
            "annual_premium": round(monthly_premium * 12, 2),
            "term_years": term_years,
            "total_lifetime": round(total, 2),
        }

    def _get_base_rate(self, coverage_type: str, coverage_amount: float) -> float:
        rates = {
            "term_life": coverage_amount * 0.0002,
            "whole_life": coverage_amount * 0.0015,
            "universal_life": coverage_amount * 0.0012,
            "health": 350,
            "auto": 85,
            "homeowners": 120,
            "renters": 25,
            "disability": 0.01 * 5000,
            "long_term_care": 200,
            "travel": coverage_amount * 0.001,
            "pet": 45,
        }
        return rates.get(coverage_type, 100)

    def _age_factor(self, age: int) -> float:
        if age <= 25:
            return 0.8
        if age <= 35:
            return 1.0
        if age <= 45:
            return 1.3
        if age <= 55:
            return 1.8
        if age <= 65:
            return 2.5
        return 4.0
