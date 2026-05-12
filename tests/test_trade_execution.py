import pytest
from src.trade_execution import execute_trade, calculate_position_size, get_balance, get_trade_history


@pytest.mark.asyncio
async def test_calculate_position_size():
    result = calculate_position_size(
        user_id="demo",
        symbol="AAPL",
        side="buy",
        quantity=10,
    )
    assert result["symbol"] == "AAPL"
    assert result["side"] == "buy"
    assert result["quantity"] == 10
    assert "price" in result
    assert "trade_value" in result
    assert "fees" in result
    assert "total_cost" in result
    assert "buying_power_after" in result


@pytest.mark.asyncio
async def test_calculate_position_size_no_stop_loss():
    result = calculate_position_size(
        user_id="demo",
        symbol="AAPL",
        side="buy",
        value=5000,
    )
    assert result["side"] == "buy"
    assert "total_cost" in result
    assert "fees" in result


@pytest.mark.asyncio
async def test_execute_buy_trade():
    result = execute_trade(
        user_id="demo",
        symbol="AAPL",
        side="buy",
        quantity=10,
        order_type="market",
    )
    assert result["status"] == "filled"
    assert result["trade"]["symbol"] == "AAPL"
    assert result["trade"]["side"] == "buy"
    assert result["trade"]["quantity"] == 10
    assert "trade_id" in result["trade"]


@pytest.mark.asyncio
async def test_execute_sell_trade():
    result = execute_trade(
        user_id="demo",
        symbol="MSFT",
        side="sell",
        quantity=5,
        order_type="limit",
    )
    assert result["status"] == "filled"
    assert result["trade"]["side"] == "sell"
    assert result["trade"]["order_type"] == "limit"


@pytest.mark.asyncio
async def test_get_balance():
    balance = get_balance("demo")
    assert "cash" in balance
    assert "currency" in balance
    assert "buying_power" in balance


@pytest.mark.asyncio
async def test_get_trade_history():
    execute_trade("demo", "AAPL", "buy", 10, "market")
    history = get_trade_history("demo")
    assert len(history) > 0
    assert history[0]["user_id"] == "demo"
