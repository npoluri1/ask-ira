import pytest
from src.portfolio import (
    calculate_portfolio,
    rebalance_portfolio,
    get_diversification_score,
    get_user_holdings,
)

RISK_PROFILES = {
    "conservative": {"equity": 30, "bond": 50, "cash": 20},
    "moderate": {"equity": 60, "bond": 30, "cash": 10},
    "aggressive": {"equity": 80, "bond": 15, "cash": 5},
}


def test_get_user_holdings():
    holdings = get_user_holdings("demo")
    assert len(holdings) > 0
    assert holdings[0]["symbol"] == "AAPL"


def test_calculate_portfolio():
    result = calculate_portfolio("demo")
    assert "total_value" in result
    assert "total_cost" in result
    assert "total_return" in result
    assert "total_return_pct" in result
    assert "positions" in result
    assert len(result["positions"]) > 0


def test_calculate_portfolio_positions():
    result = calculate_portfolio("demo")
    for pos in result["positions"]:
        assert "symbol" in pos
        assert "market_value" in pos
        assert "weight" in pos
        assert "pnl" in pos


def test_rebalance_portfolio():
    result = rebalance_portfolio("demo", {"equity": 60, "bond": 40})
    assert "current_allocation" in result
    assert "target_allocation" in result
    assert "suggested_trades" in result


def test_rebalance_portfolio_with_risk_profile():
    target = RISK_PROFILES["aggressive"]
    result = rebalance_portfolio("demo", target)
    assert "current_allocation" in result
    assert "target_allocation" in result


def test_get_diversification_score():
    portfolio = calculate_portfolio("demo")
    score = get_diversification_score(portfolio)
    assert 0 <= score["score"] <= 100
    assert "issues" in score
