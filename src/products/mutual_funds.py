import time
import uuid

MUTUAL_FUNDS = {
    "VFIAX": {
        "name": "Vanguard 500 Index Fund Admiral",
        "category": "Large Cap",
        "risk_level": "moderate",
        "expense_ratio": 0.04,
        "min_investment": 3000,
        "nav": 487.25,
        "ytd_return": 0.102,
        "one_year_return": 0.285,
        "three_year_return": 0.126,
        "five_year_return": 0.153,
    },
    "FXAIX": {
        "name": "Fidelity 500 Index Fund",
        "category": "Large Cap",
        "risk_level": "moderate",
        "expense_ratio": 0.015,
        "min_investment": 0,
        "nav": 189.40,
        "ytd_return": 0.101,
        "one_year_return": 0.283,
        "three_year_return": 0.124,
        "five_year_return": 0.151,
    },
    "VGTSX": {
        "name": "Vanguard Total International Stock Index Fund",
        "category": "International",
        "risk_level": "moderate",
        "expense_ratio": 0.09,
        "min_investment": 3000,
        "nav": 17.85,
        "ytd_return": 0.052,
        "one_year_return": 0.158,
        "three_year_return": 0.042,
        "five_year_return": 0.072,
    },
    "VBTLX": {
        "name": "Vanguard Total Bond Market Index Fund",
        "category": "Bond",
        "risk_level": "low",
        "expense_ratio": 0.05,
        "min_investment": 3000,
        "nav": 10.12,
        "ytd_return": -0.012,
        "one_year_return": 0.035,
        "three_year_return": -0.028,
        "five_year_return": 0.008,
    },
    "VGSLX": {
        "name": "Vanguard Real Estate Index Fund",
        "category": "Real Estate",
        "risk_level": "moderate_high",
        "expense_ratio": 0.12,
        "min_investment": 3000,
        "nav": 96.50,
        "ytd_return": 0.042,
        "one_year_return": 0.112,
        "three_year_return": 0.048,
        "five_year_return": 0.065,
    },
    "VIGAX": {
        "name": "Vanguard Growth Index Fund Admiral",
        "category": "Large Cap Growth",
        "risk_level": "high",
        "expense_ratio": 0.05,
        "min_investment": 3000,
        "nav": 92.30,
        "ytd_return": 0.152,
        "one_year_return": 0.385,
        "three_year_return": 0.098,
        "five_year_return": 0.172,
    },
    "PRGFX": {
        "name": "T. Rowe Price Growth Stock Fund",
        "category": "Large Cap Growth",
        "risk_level": "high",
        "expense_ratio": 0.63,
        "min_investment": 2500,
        "nav": 128.75,
        "ytd_return": 0.138,
        "one_year_return": 0.342,
        "three_year_return": 0.085,
        "five_year_return": 0.158,
    },
    "DODGX": {
        "name": "Dodge & Cox Stock Fund",
        "category": "Large Cap Value",
        "risk_level": "moderate",
        "expense_ratio": 0.52,
        "min_investment": 2500,
        "nav": 215.60,
        "ytd_return": 0.082,
        "one_year_return": 0.225,
        "three_year_return": 0.115,
        "five_year_return": 0.132,
    },
    "VWIGX": {
        "name": "Vanguard International Growth Fund",
        "category": "International Growth",
        "risk_level": "high",
        "expense_ratio": 0.42,
        "min_investment": 3000,
        "nav": 42.15,
        "ytd_return": 0.065,
        "one_year_return": 0.182,
        "three_year_return": 0.038,
        "five_year_return": 0.088,
    },
    "VFSUX": {
        "name": "Vanguard Short-Term Investment-Grade Fund",
        "category": "Short Term Bond",
        "risk_level": "low",
        "expense_ratio": 0.10,
        "min_investment": 3000,
        "nav": 10.78,
        "ytd_return": 0.018,
        "one_year_return": 0.052,
        "three_year_return": 0.012,
        "five_year_return": 0.018,
    },
}

FUND_HOLDINGS_DB: dict[str, list[dict]] = {}


class MutualFundsEngine:
    def get_funds(self) -> dict:
        return MUTUAL_FUNDS

    def get_fund(self, fund_id: str) -> dict | None:
        return MUTUAL_FUNDS.get(fund_id.upper())

    def buy_fund(self, user_id: str, fund_id: str, amount: float) -> dict:
        fund = MUTUAL_FUNDS.get(fund_id.upper())
        if not fund:
            raise ValueError(f"Fund not found: {fund_id}")
        if amount < fund["min_investment"]:
            raise ValueError(f"Minimum investment is ${fund['min_investment']:,}")

        nav = fund["nav"]
        units = round(amount / nav, 4)
        holding = {
            "holding_id": f"MFH{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "fund_id": fund_id.upper(),
            "fund_name": fund["name"],
            "category": fund["category"],
            "units": units,
            "nav": nav,
            "invested_amount": round(amount, 2),
            "current_value": round(units * nav, 2),
            "purchase_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "expense_ratio": fund["expense_ratio"],
        }

        if user_id not in FUND_HOLDINGS_DB:
            FUND_HOLDINGS_DB[user_id] = []
        FUND_HOLDINGS_DB[user_id].append(holding)
        return holding

    def get_holdings(self, user_id: str) -> list[dict]:
        holdings = FUND_HOLDINGS_DB.get(user_id, [])
        total_value = sum(h["current_value"] for h in holdings)

        result = []
        for h in holdings:
            nav = MUTUAL_FUNDS.get(h["fund_id"], {}).get("nav", h["nav"])
            current_value = round(h["units"] * nav, 2)
            pnl = round(current_value - h["invested_amount"], 2)
            pnl_pct = round((pnl / h["invested_amount"]) * 100, 2) if h["invested_amount"] else 0
            result.append({
                **h,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "weight": round(current_value / total_value * 100, 2) if total_value else 0,
            })
            h["current_value"] = current_value

        return result

    def get_portfolio_summary(self, user_id: str) -> dict:
        holdings = self.get_holdings(user_id)
        total_value = sum(h["current_value"] for h in holdings)
        total_invested = sum(h["invested_amount"] for h in holdings)
        total_pnl = round(total_value - total_invested, 2)

        by_category: dict[str, dict] = {}
        for h in holdings:
            cat = h.get("category", "Other")
            if cat not in by_category:
                by_category[cat] = {"invested": 0, "value": 0}
            by_category[cat]["invested"] += h["invested_amount"]
            by_category[cat]["value"] += h["current_value"]

        return {
            "user_id": user_id,
            "total_holdings": len(holdings),
            "total_invested": round(total_invested, 2),
            "total_value": round(total_value, 2),
            "total_pnl": total_pnl,
            "total_pnl_pct": round(total_pnl / total_invested * 100, 2) if total_invested else 0,
            "allocation_by_category": {k: round(v["value"] / total_value * 100, 2) if total_value else 0 for k, v in by_category.items()},
        }

    def create_demo_data(self, user_id: str):
        self.buy_fund(user_id, "VFIAX", 50000)
        self.buy_fund(user_id, "VBTLX", 15000)
        self.buy_fund(user_id, "VIGAX", 25000)
