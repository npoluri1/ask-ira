import random
import time
import uuid
from typing import Any

TRANSACTION_DB: dict[str, list[dict]] = {}

MERCHANT_CATEGORIES = {
    "Food & Dining": ["Starbucks", "McDonalds", "Whole Foods", "Trader Joe's", "Chipotle", "DoorDash", "Uber Eats"],
    "Shopping": ["Amazon", "Walmart", "Target", "Costco", "Best Buy", "Nike", "Zara"],
    "Transportation": ["Uber", "Lyft", "Shell", "Exxon", "BP", "City Transit", "Parking"],
    "Entertainment": ["Netflix", "Spotify", "Disney+", "HBO Max", "AMC Theaters", "Steam"],
    "Bills & Utilities": ["Electric Co", "Water Utility", "Internet Provider", "Phone Bill", "Insurance"],
    "Healthcare": ["CVS", "Walgreens", "Dr. Smith Medical", "Pharmacy"],
    "Travel": ["Delta Airlines", "Marriott", "Expedia", "Airbnb", "Hertz"],
}


class TransactionsEngine:
    def get_transactions(self, user_id: str, account_id: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
        all_tx = TRANSACTION_DB.get(user_id, [])
        if account_id:
            all_tx = [t for t in all_tx if t["account_id"] == account_id]
        return list(reversed(all_tx))[offset:offset + limit]

    def add_transaction(self, user_id: str, account_id: str, amount: float, description: str, category: str, transaction_type: str = "debit", status: str = "completed") -> dict:
        tx = {
            "transaction_id": f"TX{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "account_id": account_id,
            "amount": round(abs(amount), 2),
            "description": description,
            "category": category,
            "transaction_type": transaction_type,
            "status": status,
            "merchant": self._extract_merchant(description, category),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pending": status == "pending",
        }
        if user_id not in TRANSACTION_DB:
            TRANSACTION_DB[user_id] = []
        TRANSACTION_DB[user_id].append(tx)
        return tx

    def get_spending_summary(self, user_id: str, days: int = 30) -> dict:
        all_tx = TRANSACTION_DB.get(user_id, [])
        now = time.time()
        recent = [t for t in all_tx if now - time.mktime(time.strptime(t["timestamp"], "%Y-%m-%dT%H:%M:%SZ")) < days * 86400]

        by_category: dict[str, float] = {}
        total = 0
        for t in recent:
            if t["transaction_type"] == "debit":
                by_category[t["category"]] = by_category.get(t["category"], 0) + t["amount"]
                total += t["amount"]

        return {
            "user_id": user_id,
            "period_days": days,
            "total_spent": round(total, 2),
            "transaction_count": len(recent),
            "average_per_day": round(total / days, 2),
            "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
            "top_merchants": self._top_merchants(recent, 5),
        }

    def create_demo_data(self, user_id: str, account_ids: list[str]):
        checking_id = account_ids[0] if account_ids else ""
        if not checking_id:
            return

        for _ in range(20):
            category = random.choice(list(MERCHANT_CATEGORIES.keys()))
            merchant = random.choice(MERCHANT_CATEGORIES[category])
            amount = round(random.uniform(5, 200), 2)
            tx_type = random.choice(["debit", "debit", "debit", "credit"])
            if tx_type == "credit":
                amount = round(random.uniform(100, 2000), 2)

            self.add_transaction(
                user_id=user_id,
                account_id=checking_id,
                amount=amount,
                description=merchant,
                category=category,
                transaction_type=tx_type,
            )

    def _extract_merchant(self, description: str, category: str) -> str:
        for merch_list in MERCHANT_CATEGORIES.values():
            for m in merch_list:
                if m.lower() in description.lower():
                    return m
        return description

    def _top_merchants(self, transactions: list[dict], n: int) -> list[dict]:
        by_merchant: dict[str, float] = {}
        for t in transactions:
            if t["transaction_type"] == "debit":
                by_merchant[t["merchant"]] = by_merchant.get(t["merchant"], 0) + t["amount"]
        return [{"merchant": k, "total": round(v, 2)} for k, v in sorted(by_merchant.items(), key=lambda x: -x[1])[:n]]
