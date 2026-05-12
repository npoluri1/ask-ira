import time
import uuid
from typing import Any

BILL_CATEGORIES = {
    "utilities": ["Electric Company", "Water Utility", "Gas Company", "Internet Provider", "Cable TV"],
    "insurance": ["Health Insurance", "Auto Insurance", "Home Insurance", "Life Insurance"],
    "subscriptions": ["Netflix", "Spotify", "Apple Music", "Adobe Creative Cloud", "Microsoft 365"],
    "loans": ["Personal Loan EMI", "Auto Loan EMI", "Mortgage Payment", "Student Loan"],
    "other": ["Property Tax", "HOA Dues", "Tuition", "Childcare", "Gym Membership"],
}

BILLS_DB: dict[str, list[dict]] = {}


class BillsEngine:
    def get_bill_templates(self) -> dict:
        return BILL_CATEGORIES

    def add_bill(self, user_id: str, biller_name: str, category: str, amount: float, due_day: int, account_id: str = "", autopay: bool = False) -> dict:
        bill = {
            "bill_id": f"BLL{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "biller_name": biller_name,
            "category": category,
            "amount": round(amount, 2),
            "due_day": due_day,
            "account_id": account_id,
            "autopay": autopay,
            "status": "active",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_paid": None,
            "next_due": self._next_due_date(due_day),
        }

        if user_id not in BILLS_DB:
            BILLS_DB[user_id] = []
        BILLS_DB[user_id].append(bill)
        return bill

    def get_bills(self, user_id: str) -> list[dict]:
        return BILLS_DB.get(user_id, [])

    def pay_bill(self, user_id: str, bill_id: str) -> dict:
        for bill in BILLS_DB.get(user_id, []):
            if bill["bill_id"] == bill_id:
                bill["last_paid"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                bill["next_due"] = self._next_due_date(bill["due_day"], bill.get("next_due", ""))
                return {
                    "bill_id": bill_id,
                    "biller_name": bill["biller_name"],
                    "amount": bill["amount"],
                    "paid_at": bill["last_paid"],
                    "next_due": bill["next_due"],
                }
        raise ValueError("Bill not found")

    def get_upcoming_bills(self, user_id: str, days: int = 30) -> list[dict]:
        import datetime
        now = datetime.date.today()
        end = now + datetime.timedelta(days=days)
        upcoming = []
        for bill in BILLS_DB.get(user_id, []):
            if bill["status"] != "active":
                continue
            due_str = bill.get("next_due", "")
            if due_str:
                due_date = datetime.date.fromisoformat(due_str[:10]) if "-" in due_str else now
            else:
                due_date = now.replace(day=min(bill["due_day"], 28))
            if now <= due_date <= end:
                upcoming.append({**bill, "due_date": due_date.isoformat(), "days_until_due": (due_date - now).days})
        return sorted(upcoming, key=lambda x: x["days_until_due"])

    def get_monthly_bill_summary(self, user_id: str) -> dict:
        bills = self.get_bills(user_id)
        total = sum(b["amount"] for b in bills if b["status"] == "active")
        by_category: dict[str, float] = {}
        for b in bills:
            if b["status"] == "active":
                by_category[b["category"]] = by_category.get(b["category"], 0) + b["amount"]
        return {
            "user_id": user_id,
            "active_bills": sum(1 for b in bills if b["status"] == "active"),
            "total_monthly": round(total, 2),
            "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
            "autopay_enabled": sum(1 for b in bills if b["autopay"]),
        }

    def create_demo_data(self, user_id: str):
        bills_data = [
            ("Electric Company", "utilities", 145.00, 15),
            ("Internet Provider", "utilities", 79.99, 5),
            ("Netflix", "subscriptions", 15.99, 12),
            ("Spotify", "subscriptions", 9.99, 10),
            ("Health Insurance", "insurance", 450.00, 1),
            ("Personal Loan EMI", "loans", 485.00, 7),
        ]
        for name, cat, amt, day in bills_data:
            self.add_bill(user_id, name, cat, amt, day)

    def _next_due_date(self, due_day: int, from_date: str = "") -> str:
        import datetime
        if from_date:
            base = datetime.date.fromisoformat(from_date[:10])
            month = base.month + 1 if base.month < 12 else 1
            year = base.year if base.month < 12 else base.year + 1
        else:
            today = datetime.date.today()
            month = today.month if today.day <= due_day else today.month + 1
            year = today.year if month <= 12 else today.year + 1
            if month > 12:
                month = 1
        day = min(due_day, 28)
        return datetime.date(year, month, day).isoformat()
