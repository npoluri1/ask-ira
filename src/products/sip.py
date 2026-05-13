import time
import uuid

SIP_DB: dict[str, list[dict]] = {}
SIP_FREQUENCIES = ["daily", "weekly", "monthly", "quarterly"]

TOP_SIP_FUNDS = [
    {"fund_id": "VFIAX", "name": "Vanguard 500 Index Fund", "category": "Large Cap", "expense_ratio": 0.04, "min_sip": 100},
    {"fund_id": "VIGAX", "name": "Vanguard Growth Index Fund", "category": "Large Cap Growth", "expense_ratio": 0.05, "min_sip": 100},
    {"fund_id": "VGTSX", "name": "Vanguard Total International Stock", "category": "International", "expense_ratio": 0.09, "min_sip": 100},
    {"fund_id": "VBTLX", "name": "Vanguard Total Bond Market", "category": "Bond", "expense_ratio": 0.05, "min_sip": 100},
    {"fund_id": "DODGX", "name": "Dodge & Cox Stock Fund", "category": "Large Cap Value", "expense_ratio": 0.52, "min_sip": 100},
]


class SIPEngine:
    def get_sip_funds(self) -> list[dict]:
        return TOP_SIP_FUNDS

    def calculate_sip(self, monthly_amount: float, expected_return: float = 0.12, years: int = 10) -> dict:
        monthly_rate = expected_return / 12
        total_months = years * 12
        future_value = monthly_amount * ((1 + monthly_rate) ** total_months - 1) / monthly_rate * (1 + monthly_rate)
        total_invested = monthly_amount * total_months
        estimated_returns = future_value - total_invested

        schedule = []
        for y in range(1, years + 1):
            months = y * 12
            fv = monthly_amount * ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
            schedule.append({
                "year": y,
                "invested": round(monthly_amount * months, 2),
                "value": round(fv, 2),
                "returns": round(fv - monthly_amount * months, 2),
            })

        return {
            "monthly_amount": round(monthly_amount, 2),
            "expected_return_pct": round(expected_return * 100, 2),
            "years": years,
            "total_invested": round(total_invested, 2),
            "estimated_value": round(future_value, 2),
            "estimated_returns": round(estimated_returns, 2),
            "xirr": round(expected_return * 100, 2),
            "schedule": schedule,
        }

    def start_sip(self, user_id: str, fund_id: str, monthly_amount: float, frequency: str = "monthly") -> dict:
        if frequency not in SIP_FREQUENCIES:
            raise ValueError(f"Invalid frequency. Use: {', '.join(SIP_FREQUENCIES)}")

        fund = next((f for f in TOP_SIP_FUNDS if f["fund_id"] == fund_id), None)
        if not fund:
            raise ValueError(f"Invalid fund: {fund_id}")
        if monthly_amount < fund["min_sip"]:
            raise ValueError(f"Minimum SIP amount is ${fund['min_sip']}")

        sip = {
            "sip_id": f"SIP{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "fund_id": fund_id,
            "fund_name": fund["name"],
            "category": fund["category"],
            "monthly_amount": round(monthly_amount, 2),
            "frequency": frequency,
            "status": "active",
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "next_installment": time.strftime("%Y-%m-%d", time.gmtime(time.time() + 30 * 86400)),
            "total_installments": 0,
            "total_invested": 0,
            "total_units": 0,
        }

        if user_id not in SIP_DB:
            SIP_DB[user_id] = []
        SIP_DB[user_id].append(sip)
        return sip

    def get_sips(self, user_id: str) -> list[dict]:
        return reversed(SIP_DB.get(user_id, []))

    def stop_sip(self, user_id: str, sip_id: str) -> dict:
        for s in SIP_DB.get(user_id, []):
            if s["sip_id"] == sip_id:
                s["status"] = "stopped"
                s["stopped_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                return s
        raise ValueError("SIP not found")

    def get_portfolio_summary(self, user_id: str) -> dict:
        sips = list(SIP_DB.get(user_id, []))
        active_sips = [s for s in sips if s["status"] == "active"]
        total_monthly = sum(s["monthly_amount"] for s in active_sips)
        total_invested = sum(s.get("total_invested", 0) for s in sips)

        calc = self.calculate_sip(total_monthly, 0.12, 10) if total_monthly else {}

        return {
            "user_id": user_id,
            "active_sips": len(active_sips),
            "total_monthly_investment": round(total_monthly, 2),
            "total_invested_all_time": round(total_invested, 2),
            "projected_10y_value": calc.get("estimated_value", 0),
            "projected_10y_returns": calc.get("estimated_returns", 0),
        }

    def create_demo_data(self, user_id: str):
        self.start_sip(user_id, "VFIAX", 5000)
        self.start_sip(user_id, "VIGAX", 3000)
