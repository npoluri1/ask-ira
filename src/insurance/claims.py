import time
import uuid
from typing import Any

CLAIMS_DB: dict[str, list[dict]] = {}
CLAIM_STATUSES = ["filed", "under_review", "approved", "paid", "denied", "appealed"]


class ClaimsEngine:
    def file_claim(self, user_id: str, policy_id: str, claim_amount: float, description: str, claim_type: str = "standard") -> dict:
        claim = {
            "claim_id": f"CLM{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "policy_id": policy_id,
            "claim_amount": round(claim_amount, 2),
            "approved_amount": None,
            "description": description,
            "claim_type": claim_type,
            "status": "filed",
            "filed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "estimated_payout": None,
            "documents_required": [],
        }

        if user_id not in CLAIMS_DB:
            CLAIMS_DB[user_id] = []
        CLAIMS_DB[user_id].append(claim)
        return claim

    def get_claims(self, user_id: str, policy_id: str | None = None) -> list[dict]:
        claims = CLAIMS_DB.get(user_id, [])
        if policy_id:
            claims = [c for c in claims if c["policy_id"] == policy_id]
        return list(reversed(claims))

    def get_claim(self, user_id: str, claim_id: str) -> dict | None:
        for c in CLAIMS_DB.get(user_id, []):
            if c["claim_id"] == claim_id:
                return c
        return None

    def process_claim(self, user_id: str, claim_id: str, decision: str, approved_amount: float | None = None, reason: str = "") -> dict:
        claim = self.get_claim(user_id, claim_id)
        if not claim:
            raise ValueError("Claim not found")

        if decision == "approve":
            claim["status"] = "approved"
            claim["approved_amount"] = approved_amount or claim["claim_amount"]
            claim["estimated_payout"] = claim["approved_amount"]
        elif decision == "deny":
            claim["status"] = "denied"
            claim["denial_reason"] = reason
        elif decision == "pay":
            claim["status"] = "paid"
            claim["approved_amount"] = approved_amount or claim.get("approved_amount", claim["claim_amount"])
            claim["paid_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        else:
            raise ValueError(f"Invalid decision: {decision}")

        claim["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return claim

    def get_claims_summary(self, user_id: str) -> dict:
        claims = CLAIMS_DB.get(user_id, [])
        total_filed = len(claims)
        total_claimed = sum(c["claim_amount"] for c in claims)
        total_approved = sum(c.get("approved_amount", 0) for c in claims if c["approved_amount"])
        by_status: dict[str, int] = {}
        for c in claims:
            by_status[c["status"]] = by_status.get(c["status"], 0) + 1
        return {
            "user_id": user_id,
            "total_claims": total_filed,
            "total_claimed": round(total_claimed, 2),
            "total_approved": round(total_approved, 2),
            "approval_rate": round(total_approved / total_claimed * 100, 2) if total_claimed else 0,
            "by_status": by_status,
        }

    def create_demo_data(self, user_id: str, policy_ids: list[str]):
        if policy_ids:
            self.file_claim(user_id, policy_ids[2], 1200, "Minor collision, rear bumper damage", "auto")
            self.file_claim(user_id, policy_ids[3], 350, "Trip delay due to weather", "travel")
