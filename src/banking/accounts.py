import time
import uuid
from typing import Any

ACCOUNT_TYPES = ["checking", "savings", "joint_checking", "money_market", "student"]
ACCOUNT_CURRENCIES = ["USD", "EUR", "GBP", "INR", "SGD", "JPY"]

ACCOUNTS_DB: dict[str, list[dict]] = {}
INTEREST_RATES: dict[str, float] = {
    "checking": 0.001,
    "savings": 0.045,
    "money_market": 0.052,
    "student": 0.025,
    "joint_checking": 0.001,
}


def _next_account_number() -> str:
    return f"IRA{int(time.time())}{uuid.uuid4().hex[:6].upper()}"


class AccountsEngine:
    def get_accounts(self, user_id: str) -> list[dict]:
        return ACCOUNTS_DB.get(user_id, [])

    def get_account(self, user_id: str, account_id: str) -> dict | None:
        for a in ACCOUNTS_DB.get(user_id, []):
            if a["account_id"] == account_id:
                return a
        return None

    def create_account(self, user_id: str, account_type: str, currency: str = "USD", initial_deposit: float = 0, nickname: str = "") -> dict:
        if account_type not in ACCOUNT_TYPES:
            raise ValueError(f"Invalid account type. Must be one of: {', '.join(ACCOUNT_TYPES)}")
        if currency not in ACCOUNT_CURRENCIES:
            raise ValueError(f"Invalid currency. Must be one of: {', '.join(ACCOUNT_CURRENCIES)}")

        account = {
            "account_id": _next_account_number(),
            "user_id": user_id,
            "type": account_type,
            "currency": currency,
            "nickname": nickname or f"{account_type.replace('_', ' ').title()} Account",
            "balance": initial_deposit,
            "available_balance": initial_deposit,
            "status": "active",
            "interest_rate": INTEREST_RATES.get(account_type, 0),
            "opened_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "closed_at": None,
            "features": self._get_account_features(account_type),
        }

        if user_id not in ACCOUNTS_DB:
            ACCOUNTS_DB[user_id] = []
        ACCOUNTS_DB[user_id].append(account)
        return account

    def close_account(self, user_id: str, account_id: str) -> dict:
        account = self.get_account(user_id, account_id)
        if not account:
            raise ValueError("Account not found")
        if account["balance"] > 0:
            raise ValueError("Account has balance. Transfer funds before closing.")
        account["status"] = "closed"
        account["closed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return account

    def update_balance(self, user_id: str, account_id: str, amount: float) -> dict:
        account = self.get_account(user_id, account_id)
        if not account:
            raise ValueError("Account not found")
        account["balance"] = round(account["balance"] + amount, 2)
        account["available_balance"] = round(account["available_balance"] + amount, 2)
        return account

    def apply_interest(self, user_id: str, account_id: str) -> dict:
        account = self.get_account(user_id, account_id)
        if not account:
            raise ValueError("Account not found")
        rate = account.get("interest_rate", 0)
        monthly_rate = rate / 12
        interest = round(account["balance"] * monthly_rate, 2)
        account["balance"] = round(account["balance"] + interest, 2)
        account["available_balance"] = round(account["available_balance"] + interest, 2)
        return {"account_id": account_id, "interest_earned": interest, "new_balance": account["balance"]}

    def get_account_summary(self, user_id: str) -> dict:
        accounts = self.get_accounts(user_id)
        total_balance = sum(a["balance"] for a in accounts)
        by_type: dict[str, Any] = {}
        for a in accounts:
            t = a["type"]
            if t not in by_type:
                by_type[t] = {"count": 0, "total_balance": 0}
            by_type[t]["count"] += 1
            by_type[t]["total_balance"] += a["balance"]

        return {
            "user_id": user_id,
            "total_accounts": len(accounts),
            "total_balance": round(total_balance, 2),
            "active_accounts": sum(1 for a in accounts if a["status"] == "active"),
            "breakdown_by_type": by_type,
        }

    def create_demo_data(self, user_id: str):
        if self.get_accounts(user_id):
            return
        self.create_account(user_id, "checking", initial_deposit=15420.50, nickname="Everyday Checking")
        self.create_account(user_id, "savings", initial_deposit=45000.00, nickname="High-Yield Savings")
        self.create_account(user_id, "money_market", initial_deposit=25000.00, nickname="Money Market")

    def _get_account_features(self, account_type: str) -> list[str]:
        features = {
            "checking": ["Debit Card", "Online Banking", "Mobile Deposit", "Bill Pay", "Overdraft Protection", "Direct Deposit", "Free ATM Access"],
            "savings": ["High Interest", "No Monthly Fee", "Online Transfers", "FDIC Insured", "Automatic Savings"],
            "joint_checking": ["All Checking Features", "Dual Card Holders", "Shared Online Access", "Joint Alerts"],
            "money_market": ["Competitive Rates", "Check Writing", "Higher Balance Required", "FDIC Insured", "Limited Transactions"],
            "student": ["No Minimum Balance", "No Monthly Fee", "Free ATM Access", "Budgeting Tools", "Overdraft Grace"],
        }
        return features.get(account_type, [])
