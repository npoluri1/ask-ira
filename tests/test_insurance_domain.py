import pytest

from src.insurance.claims import ClaimsEngine
from src.insurance.policies import COVERAGE_TYPES, PoliciesEngine
from src.insurance.premiums import PremiumsEngine


@pytest.mark.asyncio
async def test_create_policy():
    engine = PoliciesEngine()
    policy = engine.create_policy(
        user_id="user1",
        coverage_type="term_life",
        coverage_amount=500000,
        premium=45.00,
        term_years=20,
    )
    assert policy["coverage_type"] == "term_life"
    assert policy["coverage_amount"] == 500000
    assert policy["status"] == "active"
    assert "policy_id" in policy


@pytest.mark.asyncio
async def test_create_policy_invalid_type():
    engine = PoliciesEngine()
    with pytest.raises(ValueError):
        engine.create_policy("user1", "invalid_type", 100000, 50.00)


@pytest.mark.asyncio
async def test_get_policies():
    engine = PoliciesEngine()
    engine.create_policy("user2", "health", 250000, 350.00)
    policies = engine.get_policies("user2")
    assert len(policies) >= 1


@pytest.mark.asyncio
async def test_coverage_types():
    assert "term_life" in COVERAGE_TYPES
    assert "whole_life" in COVERAGE_TYPES
    assert "health" in COVERAGE_TYPES
    assert COVERAGE_TYPES["term_life"]["min_coverage"] == 100000


@pytest.mark.asyncio
async def test_file_claim():
    engine = PoliciesEngine()
    policy = engine.create_policy("user3", "auto", 50000, 120.00)
    claims = ClaimsEngine()
    claim = claims.file_claim(
        user_id="user3",
        policy_id=policy["policy_id"],
        claim_type="collision",
        claim_amount=5000,
        description="Car accident",
    )
    assert claim["claim_amount"] == 5000
    assert claim["status"] == "filed"
    assert claim["claim_type"] == "collision"


@pytest.mark.asyncio
async def test_process_claim_approve():
    engine = PoliciesEngine()
    policy = engine.create_policy("user4", "health", 100000, 350.00)
    claims = ClaimsEngine()
    claim = claims.file_claim("user4", policy["policy_id"], 15000, "Emergency surgery", claim_type="surgery")
    approved = claims.process_claim("user4", claim["claim_id"], "approve", approved_amount=12000)
    assert approved["status"] == "approved"
    assert "approved_amount" in approved


@pytest.mark.asyncio
async def test_process_claim_deny():
    engine = PoliciesEngine()
    policy = engine.create_policy("user5", "renters", 20000, 15.00)
    claims = ClaimsEngine()
    claim = claims.file_claim("user5", policy["policy_id"], 5000, "Stolen laptop", claim_type="theft")
    denied = claims.process_claim("user5", claim["claim_id"], "deny", reason="Policy exclusion")
    assert denied["status"] == "denied"


@pytest.mark.asyncio
async def test_calculate_premium():
    premiums = PremiumsEngine()
    result = premiums.calculate_premium(
        coverage_type="term_life",
        coverage_amount=500000,
        age=35,
        health_rating="standard",
        term_years=20,
    )
    assert "monthly_premium" in result
    assert "annual_premium" in result
    assert result["monthly_premium"] > 0


@pytest.mark.asyncio
async def test_health_insurance_coverage_features():
    assert "Hospitalization" in COVERAGE_TYPES["health"]["features"]
    assert "deductible_options" in COVERAGE_TYPES["health"]
    assert 500 in COVERAGE_TYPES["health"]["deductible_options"]
