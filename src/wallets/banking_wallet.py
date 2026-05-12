import time
import uuid
from typing import Any

BANKING_WALLETS_DB: dict[str, list[dict]] = {}

AVAILABLE_FEATURES: list[str] = [
    "multi_currency", "virtual_iban", "spending_rules", "auto_save",
    "budgeting", "open_banking_aggregation",
]

CURRENCIES: list[str] = ["USD", "EUR", "GBP", "CHF", "JPY", "SGD", "AED", "INR", "CAD", "AUD"]

BASE_CURRENCY: str = "USD"

FX_RATES: dict[str, float] = {
    "USD": 1.0, "EUR": 1.08, "GBP": 1.26, "CHF": 1.12,
    "JPY": 0.0067, "SGD": 0.74, "AED": 0.27, "INR": 0.012,
    "CAD": 0.73, "AUD": 0.65,
}

OPEN_BANKING_PROVIDERS: list[str] = ["Plaid", "Tink", "TrueLayer", "Yodlee", "Salt Edge"]

CATEGORIES: list[str] = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment",
    "Bills & Utilities", "Healthcare", "Travel", "Education",
    "Investments", "Income", "Transfer", "Other",
]


def _to_usd(amount: float, currency: str) -> float:
    rate = FX_RATES.get(currency, 1.0)
    return round(amount * rate, 2)


def _generate_iban(country: str, wallet_id: str) -> str:
    country_code = country[:2].upper()
    bank_code = "IRAB"
    account_number = wallet_id.replace("-", "")[:10].upper().ljust(10, "0")
    checksum = str(sum(ord(c) for c in f"{country_code}{bank_code}{account_number}") % 97).zfill(2)
    return f"{country_code}{checksum}{bank_code}{account_number}"


class BankingWalletEngine:
    def create_banking_wallet(
        self,
        user_id: str,
        currency: str = "USD",
        wallet_name: str = "",
        features: list[str] | None = None,
    ) -> dict[str, Any]:
        if currency not in CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        features = features or ["multi_currency"]
        invalid = [f for f in features if f not in AVAILABLE_FEATURES]
        if invalid:
            raise ValueError(f"Invalid features: {', '.join(invalid)}")

        wallet: dict[str, Any] = {
            "wallet_id": f"BWL-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "wallet_name": wallet_name or f"{currency} Wallet",
            "currency": currency,
            "features": features,
            "balances": {c: 0.0 for c in ["USD", "EUR", "GBP", "CHF"]},
            "main_balance": 0.0,
            "virtual_iban": None,
            "spending_rules": None,
            "auto_save_rule": None,
            "linked_accounts": [],
            "status": "active",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if "virtual_iban" in features:
            wallet["virtual_iban"] = _generate_iban("US", wallet["wallet_id"])

        if user_id not in BANKING_WALLETS_DB:
            BANKING_WALLETS_DB[user_id] = []
        BANKING_WALLETS_DB[user_id].append(wallet)
        return wallet

    def get_wallets(self, user_id: str) -> list[dict[str, Any]]:
        return BANKING_WALLETS_DB.get(user_id, [])

    def get_wallet(self, user_id: str, wallet_id: str) -> dict[str, Any] | None:
        for w in BANKING_WALLETS_DB.get(user_id, []):
            if w["wallet_id"] == wallet_id:
                return w
        return None

    def get_total_balance(self, user_id: str) -> dict[str, Any]:
        wallets = self.get_wallets(user_id)
        total_usd = 0.0
        by_currency: dict[str, float] = {}
        for w in wallets:
            main = w.get("main_balance", 0)
            total_usd += _to_usd(main, w["currency"])
            by_currency[w["currency"]] = by_currency.get(w["currency"], 0) + main
            for cur, bal in w.get("balances", {}).items():
                total_usd += _to_usd(bal, cur)
        return {
            "user_id": user_id,
            "total_balance_usd": round(total_usd, 2),
            "balance_by_currency": {k: round(v, 2) for k, v in by_currency.items()},
            "wallet_count": len(wallets),
        }

    def create_virtual_iban(self, wallet_id: str, country: str) -> dict[str, Any]:
        for user_wallets in BANKING_WALLETS_DB.values():
            for w in user_wallets:
                if w["wallet_id"] == wallet_id:
                    iban = _generate_iban(country, wallet_id)
                    w["virtual_iban"] = iban
                    return {"wallet_id": wallet_id, "iban": iban, "country": country, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        raise ValueError(f"Wallet {wallet_id} not found")

    def set_spending_rules(
        self, user_id: str, wallet_id: str, rules: dict[str, Any]
    ) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Wallet not found")
        if "spending_rules" not in AVAILABLE_FEATURES:
            raise ValueError("Wallet does not have spending_rules feature")

        validated: dict[str, Any] = {
            "monthly_limit": rules.get("monthly_limit", 0),
            "per_transaction_limit": rules.get("per_transaction_limit", 0),
            "allowed_categories": rules.get("allowed_categories", CATEGORIES),
            "blocked_merchants": rules.get("blocked_merchants", []),
            "geo_restrictions": rules.get("geo_restrictions", []),
            "enabled": rules.get("enabled", True),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        wallet["spending_rules"] = validated
        return {"wallet_id": wallet_id, "rules": validated}

    def set_auto_save_rule(
        self, user_id: str, wallet_id: str, rule: dict[str, Any]
    ) -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Wallet not found")

        validated: dict[str, Any] = {
            "type": rule.get("type", "percentage"),
            "value": rule.get("value", 0),
            "target_currency": rule.get("target_currency", wallet["currency"]),
            "schedule": rule.get("schedule", "daily"),
            "enabled": rule.get("enabled", True),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        wallet["auto_save_rule"] = validated
        return {"wallet_id": wallet_id, "rule": validated}

    def link_open_banking(
        self,
        user_id: str,
        wallet_id: str,
        provider: str,
        external_account_id: str,
    ) -> dict[str, Any]:
        if provider not in OPEN_BANKING_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Wallet not found")

        link: dict[str, Any] = {
            "link_id": str(uuid.uuid4()),
            "provider": provider,
            "external_account_id": external_account_id,
            "status": "connected",
            "last_synced": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "balances": {"USD": 0.0, "EUR": 0.0, "GBP": 0.0},
        }
        wallet["linked_accounts"].append(link)
        return link

    def get_aggregated_balances(self, user_id: str) -> dict[str, Any]:
        wallets = self.get_wallets(user_id)
        internal_total = sum(_to_usd(w.get("main_balance", 0), w["currency"]) for w in wallets)
        external_total = 0.0
        external_accounts: list[dict[str, Any]] = []

        for w in wallets:
            for link in w.get("linked_accounts", []):
                for cur, bal in link.get("balances", {}).items():
                    external_total += _to_usd(bal, cur)
                external_accounts.append({
                    "provider": link["provider"],
                    "external_account_id": link["external_account_id"],
                    "balances": link["balances"],
                })

        return {
            "user_id": user_id,
            "internal_balance_usd": round(internal_total, 2),
            "external_balance_usd": round(external_total, 2),
            "total_aggregated_usd": round(internal_total + external_total, 2),
            "external_accounts": external_accounts,
            "last_aggregated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def get_spending_analytics(self, user_id: str, wallet_id: str, period: str = "monthly") -> dict[str, Any]:
        wallet = self.get_wallet(user_id, wallet_id)
        if not wallet:
            raise ValueError("Wallet not found")

        spending_by_category: dict[str, float] = {cat: 0.0 for cat in CATEGORIES}
        spending_by_category["Food & Dining"] = 450.0
        spending_by_category["Transportation"] = 220.0
        spending_by_category["Shopping"] = 380.0
        spending_by_category["Bills & Utilities"] = 600.0
        spending_by_category["Entertainment"] = 150.0

        total_spent = sum(spending_by_category.values())
        budget = wallet.get("spending_rules", {}).get("monthly_limit", 5000) or 5000

        return {
            "wallet_id": wallet_id,
            "period": period,
            "total_spent": round(total_spent, 2),
            "monthly_budget": budget,
            "budget_remaining": round(budget - total_spent, 2),
            "budget_utilization_pct": round((total_spent / budget * 100) if budget else 0, 1),
            "spending_by_category": spending_by_category,
            "top_category": max(spending_by_category, key=spending_by_category.get),
            "period_start": time.strftime("%Y-%m-01T00:00:00Z", time.gmtime()),
            "period_end": time.strftime("%Y-%m-%dT23:59:59Z", time.gmtime()),
        }

    def create_demo_data(self, user_id: str):
        if BANKING_WALLETS_DB.get(user_id):
            return
        main = self.create_banking_wallet(
            user_id, "USD", "Everyday Wallet",
            features=["multi_currency", "virtual_iban", "spending_rules", "auto_save"],
        )
        main["main_balance"] = 15420.50
        main["balances"] = {"USD": 15420.50, "EUR": 2500.00, "GBP": 1000.00}

        self.create_banking_wallet(user_id, "EUR", "Travel Wallet", features=["multi_currency", "virtual_iban"])

        savings = self.create_banking_wallet(user_id, "USD", "Savings Wallet", features=["auto_save", "budgeting"])
        savings["main_balance"] = 45000.00

        self.set_spending_rules(user_id, main["wallet_id"], {
            "monthly_limit": 5000,
            "per_transaction_limit": 1000,
            "blocked_merchants": ["Gambling sites", "Crypto mixers"],
            "geo_restrictions": ["North Korea", "Iran", "Syria"],
        })
        self.set_auto_save_rule(user_id, main["wallet_id"], {
            "type": "round_up",
            "value": 1,
            "schedule": "per_transaction",
        })
        self.link_open_banking(user_id, main["wallet_id"], "Plaid", "EXT-ACC-001")
