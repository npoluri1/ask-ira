import time
import uuid

ANNUITY_PRODUCTS = {
    "immediate_fixed": {
        "name": "Immediate Fixed Annuity",
        "description": "Guaranteed income starting immediately",
        "min_investment": 25000,
        "max_investment": 2000000,
        "payout_options": ["life_only", "life_with_period", "joint_life", "period_certain"],
        "payout_frequencies": ["monthly", "quarterly", "semi_annual", "annual"],
    },
    "deferred_fixed": {
        "name": "Deferred Fixed Annuity",
        "description": "Tax-deferred growth with guaranteed returns",
        "min_investment": 10000,
        "max_investment": 1000000,
        "guaranteed_rate": 0.035,
        "deferral_periods": [1, 3, 5, 10],
        "surrender_charge_period": [5, 7, 10],
    },
    "variable": {
        "name": "Variable Annuity",
        "description": "Market-linked growth potential",
        "min_investment": 5000,
        "max_investment": 5000000,
        "sub_account_options": ["Equity Growth", "Balanced", "Bond Income", "International", "Money Market"],
        "death_benefit_options": ["return_of_premium", "step_up", "enhanced"],
        "rider_options": ["GMIB", "GMWB", "GMLB", "GLWB"],
    },
    "indexed": {
        "name": "Fixed Indexed Annuity",
        "description": "Index-linked returns with downside protection",
        "min_investment": 10000,
        "max_investment": 2000000,
        "index_options": ["S&P 500", "NASDAQ 100", "Russell 2000", "Bloomberg Bond"],
        "participation_rate": 0.85,
        "cap_rate": 0.10,
        "floor_rate": 0.0,
    },
    "qualified_longevity": {
        "name": "Qualified Longevity Annuity Contract (QLAC)",
        "description": "Deferred income starting at age 85, reduces RMD",
        "min_investment": 25000,
        "max_investment": 200000,
        "max_deferral_years": 40,
        "tax_qualified": True,
    },
}

ANNUITY_HOLDINGS_DB: dict[str, list[dict]] = {}


class AnnuitiesEngine:
    def get_products(self) -> dict:
        return ANNUITY_PRODUCTS

    def calculate_payout(self, annuity_type: str, investment: float, payout_option: str = "life_only", age: int = 65, term_years: int | None = None) -> dict:
        base_factor = self._get_payout_factor(annuity_type, age, payout_option)
        if annuity_type == "immediate_fixed":
            annual_payout = investment * base_factor
            monthly_payout = annual_payout / 12
            return {
                "annuity_type": annuity_type,
                "investment": round(investment, 2),
                "payout_option": payout_option,
                "annual_payout": round(annual_payout, 2),
                "monthly_payout": round(monthly_payout, 2),
                "payout_rate": round(base_factor * 100, 2),
            }
        elif annuity_type == "deferred_fixed":
            rate = ANNUITY_PRODUCTS["deferred_fixed"]["guaranteed_rate"]
            deferral = term_years or 10
            future_value = investment * (1 + rate) ** deferral
            annual_payout = future_value * base_factor
            return {
                "annuity_type": annuity_type,
                "investment": round(investment, 2),
                "deferral_years": deferral,
                "guaranteed_rate": rate,
                "future_value": round(future_value, 2),
                "annual_payout": round(annual_payout, 2),
                "monthly_payout": round(annual_payout / 12, 2),
            }
        return {"error": "Calculation not available for this annuity type"}

    def purchase(self, user_id: str, annuity_type: str, investment: float, payout_option: str = "life_only", age: int = 60, deferral_years: int = 10) -> dict:
        product = ANNUITY_PRODUCTS.get(annuity_type)
        if not product:
            raise ValueError(f"Invalid annuity: {annuity_type}")
        if investment < product.get("min_investment", 0):
            raise ValueError(f"Minimum investment is ${product['min_investment']:,}")

        payout = self.calculate_payout(annuity_type, investment, payout_option, age, deferral_years)
        contract = {
            "contract_id": f"ANN{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "annuity_type": annuity_type,
            "product_name": product["name"],
            "investment": round(investment, 2),
            "payout_option": payout_option,
            "annuitant_age": age,
            "deferral_years": deferral_years if annuity_type in ("deferred_fixed", "qualified_longevity") else 0,
            "payout_details": payout,
            "status": "active",
            "purchase_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "income_start_date": time.strftime("%Y-%m-%d", time.gmtime(time.time() + (deferral_years * 365 * 86400))) if annuity_type in ("deferred_fixed", "qualified_longevity") else time.strftime("%Y-%m-%d", time.gmtime()),
        }

        if user_id not in ANNUITY_HOLDINGS_DB:
            ANNUITY_HOLDINGS_DB[user_id] = []
        ANNUITY_HOLDINGS_DB[user_id].append(contract)
        return contract

    def get_holdings(self, user_id: str) -> list[dict]:
        return ANNUITY_HOLDINGS_DB.get(user_id, [])

    def get_portfolio_summary(self, user_id: str) -> dict:
        holdings = self.get_holdings(user_id)
        total_invested = sum(h["investment"] for h in holdings if h["status"] == "active")
        total_annual_income = sum(
            h.get("payout_details", {}).get("annual_payout", 0)
            for h in holdings
            if h["status"] == "active" and h.get("payout_details")
        )
        return {
            "user_id": user_id,
            "active_contracts": sum(1 for h in holdings if h["status"] == "active"),
            "total_invested": round(total_invested, 2),
            "total_annual_income": round(total_annual_income, 2),
            "total_monthly_income": round(total_annual_income / 12, 2),
        }

    def _get_payout_factor(self, annuity_type: str, age: int, payout_option: str) -> float:
        if payout_option == "life_only":
            if age >= 75:
                return 0.08
            if age >= 65:
                return 0.065
            if age >= 55:
                return 0.05
            return 0.035
        elif payout_option == "joint_life":
            return self._get_payout_factor(annuity_type, age, "life_only") * 0.85
        elif payout_option == "period_certain":
            return 0.06
        elif payout_option == "life_with_period":
            return 0.058
        return 0.05

    def create_demo_data(self, user_id: str):
        self.purchase(user_id, "immediate_fixed", 100000, "life_only", age=65)
        self.purchase(user_id, "deferred_fixed", 50000, "life_only", age=50, deferral_years=15)
