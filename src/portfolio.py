import time
from decimal import Decimal
from typing import Any

DEFAULT_HOLDINGS: dict[str, list[dict]] = {
    "demo": [
        {"symbol": "AAPL", "shares": 50, "avg_cost": 165.0},
        {"symbol": "MSFT", "shares": 30, "avg_cost": 380.0},
        {"symbol": "VTI",  "shares": 20, "avg_cost": 245.0},
        {"symbol": "BND",  "shares": 40, "avg_cost": 72.0},
    ],
    "admin": [
        {"symbol": "NVDA", "shares": 25, "avg_cost": 620.0},
        {"symbol": "AMZN", "shares": 15, "avg_cost": 170.0},
        {"symbol": "GOOGL", "shares": 20, "avg_cost": 135.0},
        {"symbol": "TSLA", "shares": 10, "avg_cost": 220.0},
        {"symbol": "VTI",  "shares": 50, "avg_cost": 245.0},
        {"symbol": "BND",  "shares": 30, "avg_cost": 72.0},
    ],
}


def get_current_price(symbol: str) -> float:
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        hist = t.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        info = t.info or {}
        return info.get("currentPrice") or info.get("regularMarketPrice") or 100
    except Exception:
        from src.config.data_source import is_seed
        if is_seed():
            from src.api.market_routes import SEED_PRICES
            if symbol.upper() in SEED_PRICES:
                return SEED_PRICES[symbol.upper()]["price"]
        return 100


def get_user_holdings(user_id: str) -> list[dict]:
    return DEFAULT_HOLDINGS.get(user_id, DEFAULT_HOLDINGS.get("demo", []))


def calculate_portfolio(user_id: str) -> dict[str, Any]:
    holdings = get_user_holdings(user_id)
    total_value = Decimal("0")
    total_cost = Decimal("0")
    positions = []

    for h in holdings:
        price = Decimal(str(get_current_price(h["symbol"])))
        shares = Decimal(str(h["shares"]))
        avg_cost = Decimal(str(h["avg_cost"]))
        market_value = price * shares
        cost_basis = avg_cost * shares
        pnl = market_value - cost_basis
        pnl_pct = float((pnl / cost_basis) * 100) if cost_basis else 0
        total_value += market_value
        total_cost += cost_basis

        positions.append({
            "symbol": h["symbol"],
            "shares": int(shares),
            "avg_cost": float(avg_cost),
            "current_price": float(price),
            "market_value": float(market_value),
            "cost_basis": float(cost_basis),
            "pnl": float(pnl),
            "pnl_pct": round(pnl_pct, 2),
            "weight": 0,
        })

    for p in positions:
        p["weight"] = round(p["market_value"] / float(total_value) * 100, 2) if total_value else 0

    total_return = float(total_value - total_cost)
    total_return_pct = round((total_return / float(total_cost)) * 100, 2) if total_cost else 0

    return {
        "user_id": user_id,
        "total_value": float(round(total_value, 2)),
        "total_cost": float(round(total_cost, 2)),
        "total_return": round(total_return, 2),
        "total_return_pct": total_return_pct,
        "positions": positions,
        "position_count": len(positions),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def rebalance_portfolio(user_id: str, target_allocations: dict[str, float]) -> dict[str, Any]:
    portfolio = calculate_portfolio(user_id)
    current_holdings = get_user_holdings(user_id)
    current_map = {h["symbol"]: h for h in current_holdings}

    trades = []
    total_value = Decimal(str(portfolio["total_value"]))

    for symbol, target_pct in target_allocations.items():
        target_value = float(total_value) * (target_pct / 100)
        if symbol in current_map:
            current_value = current_map[symbol]["shares"] * get_current_price(symbol)
            diff = target_value - current_value
            if abs(diff) > 100:
                trades.append({
                    "symbol": symbol,
                    "action": "buy" if diff > 0 else "sell",
                    "value": round(abs(diff), 2),
                    "reason": f"Rebalance from {round(current_value,2)} to {round(target_value,2)}",
                })
        else:
            trades.append({
                "symbol": symbol,
                "action": "buy",
                "value": round(target_value, 2),
                "reason": "New position",
            })

    return {
        "user_id": user_id,
        "current_allocation": {p["symbol"]: p["weight"] for p in portfolio["positions"]},
        "target_allocation": target_allocations,
        "suggested_trades": trades,
        "trade_count": len(trades),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def get_diversification_score(portfolio: dict) -> dict:
    positions = portfolio.get("positions", [])
    if not positions:
        return {"score": 0, "grade": "F", "issues": ["No holdings"]}

    weights = [p["weight"] for p in positions]
    max_weight = max(weights) if weights else 0
    position_count = len(positions)

    score = 100
    issues = []

    if max_weight > 40:
        score -= 30
        issues.append(f"Over-concentrated: top holding is {max_weight:.1f}%")
    elif max_weight > 25:
        score -= 15
        issues.append(f"Moderate concentration: top holding is {max_weight:.1f}%")

    if position_count < 3:
        score -= 25
        issues.append("Too few positions (< 3)")
    elif position_count < 5:
        score -= 10
        issues.append("Consider adding more positions (aim for 5+)")

    score = max(0, min(100, score))

    grade = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D" if score >= 20 else "F"

    return {"score": score, "grade": grade, "issues": issues}
