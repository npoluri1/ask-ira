import time
import uuid
from typing import Any

from .accounts import AccountsEngine

TRANSFER_TYPES = ["internal", "wire", "ach", "external"]
TRANSFER_DB: dict[str, list[dict]] = {}

accounts_engine = AccountsEngine()


class TransfersEngine:
    def initiate_transfer(self, user_id: str, from_account: str, to_account: str, amount: float, transfer_type: str = "internal", description: str = "", scheduled_date: str | None = None) -> dict:
        if transfer_type not in TRANSFER_TYPES:
            raise ValueError(f"Invalid transfer type: {transfer_type}")

        source = accounts_engine.get_account(user_id, from_account)
        if not source:
            raise ValueError("Source account not found")

        if source["status"] != "active":
            raise ValueError("Source account is not active")

        if source["balance"] < amount:
            raise ValueError(f"Insufficient funds. Available: ${source['balance']:.2f}, Required: ${amount:.2f}")

        transfer_id = f"TFR{uuid.uuid4().hex[:12].upper()}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        transfer = {
            "transfer_id": transfer_id,
            "user_id": user_id,
            "from_account": from_account,
            "to_account": to_account,
            "amount": round(amount, 2),
            "transfer_type": transfer_type,
            "description": description or f"Transfer {transfer_type}",
            "status": "pending" if scheduled_date else "completed",
            "scheduled_date": scheduled_date,
            "created_at": now,
            "completed_at": scheduled_date if scheduled_date else now,
        }

        if scheduled_date:
            transfer["estimated_completion"] = scheduled_date
        else:
            accounts_engine.update_balance(user_id, from_account, -amount)
            accounts_engine.update_balance(user_id, to_account, amount)

        if user_id not in TRANSFER_DB:
            TRANSFER_DB[user_id] = []
        TRANSFER_DB[user_id].append(transfer)

        return transfer

    def cancel_scheduled(self, user_id: str, transfer_id: str) -> dict:
        for t in TRANSFER_DB.get(user_id, []):
            if t["transfer_id"] == transfer_id and t.get("scheduled_date"):
                t["status"] = "cancelled"
                return t
        raise ValueError("Scheduled transfer not found")

    def get_transfers(self, user_id: str) -> list[dict]:
        return list(reversed(TRANSFER_DB.get(user_id, [])))

    def get_transfer_fees(self, transfer_type: str, amount: float) -> dict:
        fees = {
            "internal": {"fee": 0, "estimated_time": "Instant"},
            "ach": {"fee": round(amount * 0.005, 2), "estimated_time": "1-3 business days"},
            "wire": {"fee": 25.0, "estimated_time": "Same day"},
            "external": {"fee": round(amount * 0.01, 2), "estimated_time": "3-5 business days"},
        }
        return fees.get(transfer_type, fees["internal"])

    def create_demo_data(self, user_id: str):
        transfers = [
            {"from": self._get_account_id(user_id, 0), "to": self._get_account_id(user_id, 1), "amount": 500, "type": "internal", "desc": "Transfer to Savings"},
            {"from": self._get_account_id(user_id, 1), "to": self._get_account_id(user_id, 0), "amount": 200, "type": "internal", "desc": "Transfer to Checking"},
        ]
        for t in transfers:
            try:
                self.initiate_transfer(user_id, t["from"], t["to"], t["amount"], t["type"], t["desc"])
            except Exception:
                pass

    def _get_account_id(self, user_id: str, index: int) -> str:
        accts = accounts_engine.get_accounts(user_id)
        return accts[index]["account_id"] if accts else ""
