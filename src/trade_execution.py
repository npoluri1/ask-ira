import time
from decimal import Decimal
from typing import Any

TRADE_HISTORY: dict[str, list[dict]] = {}
PENDING_APPROVALS: dict[str, list[dict]] = {}
USER_BALANCES: dict[str, float] = {
    "demo": 50000.0,
    "admin": 250000.0,
}

BUYING_POWER_MULTIPLIER = 2.0
MAX_TRADE_WITHOUT_APPROVAL = 10000.0
FEE_RATE = 0.001


def get_price(symbol: str) -> float:
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


def get_balance(user_id: str) -> dict:
    balance = USER_BALANCES.get(user_id, 0)
    return {
        "user_id": user_id,
        "cash": balance,
        "buying_power": balance * BUYING_POWER_MULTIPLIER,
        "currency": "USD",
    }


def calculate_position_size(user_id: str, symbol: str, side: str, quantity: int | None = None, value: float | None = None) -> dict:
    balance = USER_BALANCES.get(user_id, 0)
    price = get_price(symbol)
    buying_power = balance * BUYING_POWER_MULTIPLIER

    if side == "buy":
        if quantity and value:
            pass
        elif quantity:
            value = quantity * price
        elif value:
            quantity = int(value / price)
        else:
            return {"error": "Specify quantity or value"}

        trade_value = quantity * price
        fees = trade_value * FEE_RATE
        total_cost = trade_value + fees

        if total_cost > buying_power:
            max_quantity = int((buying_power * 0.95) / price)
            max_value = max_quantity * price
            return {
                "symbol": symbol,
                "side": side,
                "requested_quantity": quantity,
                "max_affordable_quantity": max_quantity,
                "max_affordable_value": round(max_value, 2),
                "price": round(price, 2),
                "buying_power": round(buying_power, 2),
                "insufficient_funds": True,
                "error": f"Insufficient buying power. Max affordable: {max_quantity} shares (${max_value:.2f})",
            }

        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": round(price, 2),
            "trade_value": round(trade_value, 2),
            "fees": round(fees, 2),
            "total_cost": round(total_cost, 2),
            "buying_power_after": round(buying_power - total_cost, 2),
        }

    else:
        if quantity:
            value = quantity * price
        elif value:
            quantity = int(value / price)
        else:
            return {"error": "Specify quantity or value"}

        trade_value = quantity * price
        fees = trade_value * FEE_RATE
        total_proceeds = trade_value - fees

        from src.portfolio import get_user_holdings
        holdings = get_user_holdings(user_id)
        held = next((h for h in holdings if h["symbol"] == symbol), None)
        if not held or held["shares"] < quantity:
            return {
                "symbol": symbol,
                "side": side,
                "held": held["shares"] if held else 0,
                "requested": quantity,
                "error": f"Insufficient shares. You hold {held['shares'] if held else 0} shares of {symbol}",
            }

        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": round(price, 2),
            "trade_value": round(trade_value, 2),
            "fees": round(fees, 2),
            "total_proceeds": round(total_proceeds, 2),
        }


def execute_trade(user_id: str, symbol: str, side: str, quantity: int, order_type: str = "market") -> dict[str, Any]:
    analysis = calculate_position_size(user_id, symbol, side, quantity=quantity)
    if "error" in analysis:
        return {"status": "rejected", "reason": analysis["error"]}

    trade_value = analysis["trade_value"]
    fees = analysis["fees"]
    needs_approval = trade_value > MAX_TRADE_WITHOUT_APPROVAL

    if needs_approval:
        approval_id = f"app_{user_id}_{int(time.time())}"
        approval = {
            "approval_id": approval_id,
            "user_id": user_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "trade_value": trade_value,
            "order_type": order_type,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if user_id not in PENDING_APPROVALS:
            PENDING_APPROVALS[user_id] = []
        PENDING_APPROVALS[user_id].append(approval)
        return {
            "status": "pending_approval",
            "approval_id": approval_id,
            "message": f"Trade exceeds ${MAX_TRADE_WITHOUT_APPROVAL:,.0f}. Manual approval required.",
            "trade_details": analysis,
        }

    trade_id = f"trade_{user_id}_{int(time.time())}_{symbol}"
    trade = {
        "trade_id": trade_id,
        "user_id": user_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": analysis["price"],
        "trade_value": trade_value,
        "fees": fees,
        "total": trade_value + fees if side == "buy" else trade_value - fees,
        "order_type": order_type,
        "status": "filled",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if user_id not in TRADE_HISTORY:
        TRADE_HISTORY[user_id] = []
    TRADE_HISTORY[user_id].append(trade)

    if side == "buy":
        USER_BALANCES[user_id] = USER_BALANCES.get(user_id, 0) - trade_value - fees
    else:
        USER_BALANCES[user_id] = USER_BALANCES.get(user_id, 0) + trade_value - fees

    return {"status": "filled", "trade": trade}


def get_pending_approvals(user_id: str) -> list[dict]:
    return PENDING_APPROVALS.get(user_id, [])


def approve_trade(approval_id: str, user_id: str) -> dict:
    if user_id not in PENDING_APPROVALS:
        return {"status": "error", "message": "No pending approvals"}
    for i, a in enumerate(PENDING_APPROVALS[user_id]):
        if a["approval_id"] == approval_id:
            approved = PENDING_APPROVALS[user_id].pop(i)
            return execute_trade(user_id, approved["symbol"], approved["side"], approved["quantity"], approved["order_type"])
    return {"status": "error", "message": "Approval not found"}


def get_trade_history(user_id: str) -> list[dict]:
    return TRADE_HISTORY.get(user_id, [])
