from fastapi import APIRouter
from src.insurance import policies, claims, premiums

router = APIRouter(prefix="/api/v1/insurance")

def _get_user_id() -> str:
    return "demo"

# Seed demo data on load
policies.create_demo_data(_get_user_id())
claims.create_demo_data(_get_user_id(), [p["policy_id"] for p in policies.get_policies(_get_user_id())])


@router.get("/policies")
async def list_policies():
    return {"data": policies.get_policies(_get_user_id())}

@router.post("/policies")
async def create_policy(body: dict):
    return policies.create_policy(
        user_id=_get_user_id(),
        policy_type=body.get("policy_type", "term_life"),
        coverage_amount=body.get("coverage_amount", 100000),
        term_years=body.get("term_years", 10),
        beneficiaries=body.get("beneficiaries", []),
    )

@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str):
    return policies.get_policy(_get_user_id(), policy_id)

@router.get("/claims")
async def list_claims():
    return {"data": claims.get_claims(_get_user_id())}

@router.post("/claims")
async def file_claim(body: dict):
    return claims.file_claim(
        user_id=_get_user_id(),
        policy_id=body.get("policy_id", ""),
        claim_type=body.get("claim_type", "death"),
        amount=body.get("amount", 0),
        description=body.get("description", ""),
    )

@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    return claims.get_claim(_get_user_id(), claim_id)

@router.post("/claims/{claim_id}/approve")
async def approve_claim(claim_id: str):
    return claims.approve_claim(_get_user_id(), claim_id)

@router.post("/claims/{claim_id}/deny")
async def deny_claim(claim_id: str, body: dict):
    return claims.deny_claim(_get_user_id(), claim_id, body.get("reason", ""))

@router.get("/premiums")
async def list_premiums():
    return {"data": premiums.get_payment_history(_get_user_id())}

@router.post("/premiums/calculate")
async def calculate_premium(body: dict):
    return premiums.calculate_premium(
        policy_type=body.get("policy_type", "term_life"),
        age=body.get("age", 30),
        coverage_amount=body.get("coverage_amount", 100000),
        term_years=body.get("term_years", 10),
        health_status=body.get("health_status", "standard"),
    )

@router.get("/summary")
async def insurance_summary():
    user_id = _get_user_id()
    pol = policies.get_policies(user_id)
    cla = claims.get_claims(user_id)
    prem = premiums.get_payment_history(user_id)
    total_coverage = sum(p.get("coverage_amount", 0) for p in pol)
    active_claims = len([c for c in cla if c.get("status") == "pending"])
    return {
        "total_policies": len(pol),
        "total_coverage": total_coverage,
        "active_claims": active_claims,
        "pending_premiums": len(prem),
    }