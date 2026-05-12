import asyncio
import json
import logging
import math
import time as time_module
from datetime import datetime, timezone

import httpx
import yfinance as yf
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.api.fallback_query import (
    generate_dynamic_bond,
    generate_dynamic_commodity,
    generate_dynamic_crypto,
    generate_dynamic_forex,
    generate_dynamic_index,
    generate_dynamic_news,
    generate_dynamic_stock,
    generate_fallback_report,
)
from src.config.data_source import is_seed

logger = logging.getLogger("ask-ira.market")

router = APIRouter(prefix="/api/v1/market")

_cache: dict[str, tuple[any, float]] = {}
_CACHE_TTL = 30.0


def _cached(key: str, ttl: float = _CACHE_TTL):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            now = datetime.now(timezone.utc).timestamp()
            if key in _cache and now - _cache[key][1] < ttl:
                return _cache[key][0]
            result = await func(*args, **kwargs)
            _cache[key] = (result, now)
            return result
        return wrapper
    return decorator


def _sanitize(d: dict) -> dict:
    return {k: 0.0 if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v for k, v in d.items()}


def _fetch_ticker(ticker: str) -> dict:
    base = generate_dynamic_stock(ticker.upper())
    result = {k: v for k, v in base.items() if k != "name"}
    if is_seed():
        return result
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="2d")
        if hist.empty:
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", 0)
            prev = info.get("previousClose", price)
            change = price - prev if price and prev else 0
            change_pct = (change / prev * 100) if prev else 0
        else:
            close = hist["Close"]
            price = float(close.iloc[-1])
            prev = float(close.iloc[-2]) if len(close) > 1 else price
            change = price - prev
            change_pct = (change / prev * 100) if prev else 0
        overlay = _sanitize({
            "price": round(price, 2),
            "change": round(change, 2),
            "changePercent": round(change_pct, 2),
            "high": round(info.get("dayHigh") or hist["High"].max() if not hist.empty else price, 2),
            "low": round(info.get("dayLow") or hist["Low"].min() if not hist.empty else price, 2),
            "volume": int(hist["Volume"].iloc[-1]) if not hist.empty else info.get("volume", 0),
            "marketCap": info.get("marketCap"),
            "name": info.get("shortName") or info.get("longName") or ticker,
        })
        result.update(overlay)
    except Exception as e:
        logger.warning("yfinance enrichment failed for %s: %s — using AI-generated data", ticker, e)
    return _sanitize(result)


INDICES_MAP = {
    "SPX": "^GSPC", "IXIC": "^IXIC", "DJI": "^DJI",
    "NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK",
    "STI": "^STI", "N225": "^N225", "FTSE": "^FTSE",
    "DAX": "^GDAXI", "SHCOMP": "000001.SS", "HSI": "^HSI",
    "VIX": "^VIX",
}

FOREX_MAP = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "USDJPY=X",
    "USD/INR": "USDINR=X", "USD/SGD": "USDSGD=X", "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X", "USD/CHF": "USDCHF=X", "NZD/USD": "NZDUSD=X",
}

CRYPTO_MAP = {
    "BTC-USD": "BTC-USD", "ETH-USD": "ETH-USD", "BNB-USD": "BNB-USD",
    "XRP-USD": "XRP-USD", "ADA-USD": "ADA-USD", "SOL-USD": "SOL-USD",
    "DOT-USD": "DOT-USD", "DOGE-USD": "DOGE-USD", "AVAX-USD": "AVAX-USD",
}

COMMODITY_MAP = {
    "Gold": "GC=F", "Silver": "SI=F", "Crude Oil": "CL=F",
    "Brent Oil": "BZ=F", "Natural Gas": "NG=F", "Copper": "HG=F",
    "Platinum": "PL=F", "Palladium": "PA=F", "Wheat": "ZW=F",
}

BOND_MAP = {
    "US10Y": "^TNX", "US2Y": "2YY=F", "US30Y": "^TYX",
    "IN10Y": "IN10Y.NS", "SG10Y": "SG10Y.SI", "UK10Y": "UK10Y.SI",
    "LQD": "LQD", "HYG": "HYG",
}


@router.get("/indices")
async def get_indices():
    results = []
    for name, symbol in INDICES_MAP.items():
        s = generate_dynamic_index(name)
        if not is_seed():
            try:
                data = _sanitize(_fetch_ticker(symbol))
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/forex")
async def get_forex():
    results = []
    for name, symbol in FOREX_MAP.items():
        s = generate_dynamic_forex(name)
        if not is_seed():
            try:
                data = _sanitize(_fetch_ticker(symbol))
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/crypto")
async def get_crypto():
    results = []
    for name, symbol in CRYPTO_MAP.items():
        s = generate_dynamic_crypto(name)
        if not is_seed():
            try:
                data = _sanitize(_fetch_ticker(symbol))
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/commodities")
async def get_commodities():
    results = []
    for name, symbol in COMMODITY_MAP.items():
        s = generate_dynamic_commodity(name)
        if not is_seed():
            try:
                data = _sanitize(_fetch_ticker(symbol))
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/bonds")
async def get_bonds():
    results = []
    for name, symbol in BOND_MAP.items():
        s = generate_dynamic_bond(name)
        if not is_seed():
            try:
                data = _sanitize(_fetch_ticker(symbol))
                if name.endswith("Y") and "price" in data:
                    yf_yield = data.get("price", 0)
                    if yf_yield and yf_yield < 20:
                        data["yield"] = round(yf_yield, 2)
                        data["price"] = round(100 - ((yf_yield - 2) * 2), 2) if yf_yield > 2 else 100
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/stocks/{ticker}")
async def get_stock(ticker: str):
    return _fetch_ticker(ticker.upper())


@router.get("/stocks")
async def get_stocks():
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]
    results = []
    for s in symbols:
        try:
            data = _fetch_ticker(s)
            results.append({"symbol": s, **data})
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", s, e)
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/forex")
async def get_forex():
    results = []
    for name, symbol in FOREX_MAP.items():
        s = generate_dynamic_forex(name)
        if not is_seed():
            try:
                data = _fetch_ticker(symbol)
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/crypto")
async def get_crypto():
    results = []
    for name, symbol in CRYPTO_MAP.items():
        s = generate_dynamic_crypto(name)
        if not is_seed():
            try:
                data = _fetch_ticker(symbol)
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/commodities")
async def get_commodities():
    results = []
    for name, symbol in COMMODITY_MAP.items():
        s = generate_dynamic_commodity(name)
        if not is_seed():
            try:
                data = _fetch_ticker(symbol)
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/bonds")
async def get_bonds():
    results = []
    for name, symbol in BOND_MAP.items():
        s = generate_dynamic_bond(name)
        if not is_seed():
            try:
                data = _fetch_ticker(symbol)
                if name.endswith("Y") and "price" in data:
                    yf_yield = data.get("price", 0)
                    if yf_yield < 20:
                        data["yield"] = round(yf_yield, 2)
                        data["price"] = round(100 - ((yf_yield - 2) * 2), 2) if yf_yield > 2 else 100
                s.update(data)
            except Exception:
                pass
        results.append({"symbol": name, **s})
    return {"data": results, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": "seed" if is_seed() else "realtime"}


@router.get("/movers")
async def get_movers():
    all_stocks_data = []
    for s in ["NVDA", "AMD", "META", "AMZN", "AAPL", "INTC", "PFE", "KO", "DIS", "BA"]:
        try:
            all_stocks_data.append({"symbol": s, **_fetch_ticker(s)})
        except Exception:
            pass
    all_stocks_data.sort(key=lambda x: x.get("changePercent", 0), reverse=True)
    return {
        "gainers": all_stocks_data[:5],
        "losers": list(reversed(all_stocks_data[-5:])),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "dataSource": "seed" if is_seed() else "realtime",
    }


@router.get("/live")
async def market_live_sse(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                ds = "seed" if is_seed() else "realtime"
                j_indices = [{"symbol": k, **generate_dynamic_index(k)} for k in INDICES_MAP]
                j_stocks = [{"symbol": k, **generate_dynamic_stock(k)} for k in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]]
                j_forex = [{"symbol": k, **generate_dynamic_forex(k)} for k in FOREX_MAP]
                j_crypto = [{"symbol": k, **generate_dynamic_crypto(k)} for k in CRYPTO_MAP]
                news_data = generate_dynamic_news(5)
                if not is_seed():
                    for idx_name in INDICES_MAP:
                        try:
                            d = _fetch_ticker(INDICES_MAP[idx_name])
                            for item in j_indices:
                                if item["symbol"] == idx_name:
                                    item.update(d)
                        except Exception:
                            pass
                    for sym in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]:
                        try:
                            d = _fetch_ticker(sym)
                            for item in j_stocks:
                                if item["symbol"] == sym:
                                    item.update(d)
                        except Exception:
                            pass
                    for fx_name in FOREX_MAP:
                        try:
                            d = _fetch_ticker(FOREX_MAP[fx_name])
                            for item in j_forex:
                                if item["symbol"] == fx_name:
                                    item.update(d)
                        except Exception:
                            pass
                    for cr_name in CRYPTO_MAP:
                        try:
                            d = _fetch_ticker(CRYPTO_MAP[cr_name])
                            for item in j_crypto:
                                if item["symbol"] == cr_name:
                                    item.update(d)
                        except Exception:
                            pass
                    try:
                        async with httpx.AsyncClient() as client:
                            resp = await client.get("https://query1.finance.yahoo.com/v1/finance/news?count=5", timeout=5)
                            if resp.status_code == 200:
                                items = resp.json().get("items", {}).get("result", [])
                                ynews = [{"title": item.get("title", ""), "source": item.get("publisher", ""), "url": item.get("link", ""), "timestamp": item.get("providerPublishTime")} for item in items[:5]]
                                if ynews:
                                    news_data = ynews
                    except Exception:
                        pass
                yield f"data: {json.dumps({'type': 'indices', 'data': j_indices, 'updatedAt': datetime.now(timezone.utc).isoformat(), 'dataSource': ds})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'stocks', 'data': j_stocks, 'updatedAt': datetime.now(timezone.utc).isoformat(), 'dataSource': ds})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'forex', 'data': j_forex, 'updatedAt': datetime.now(timezone.utc).isoformat(), 'dataSource': ds})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'crypto', 'data': j_crypto, 'updatedAt': datetime.now(timezone.utc).isoformat(), 'dataSource': ds})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'news', 'data': news_data, 'updatedAt': datetime.now(timezone.utc).isoformat(), 'dataSource': ds})}\n\n"
                await asyncio.sleep(0.1)
                insights = {}
                for section in ["dashboard", "stocks", "forex", "crypto", "commodities", "bonds", "funds"]:
                    insights[section] = generate_fallback_report(section, "moderate").get("report", "")[:200]
                yield f"data: {json.dumps({'type': 'insights', 'data': insights, 'updatedAt': datetime.now(timezone.utc).isoformat(), 'dataSource': ds})}\n\n"
            except Exception:
                pass
            await asyncio.sleep(30)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@router.get("/news")
async def get_news():
    news = generate_dynamic_news(8)
    ds = "seed"
    if not is_seed():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://query1.finance.yahoo.com/v1/finance/news?count=10", timeout=10)
                if resp.status_code == 200:
                    items = resp.json().get("items", {}).get("result", [])
                    ynews = [{"title": item.get("title", ""), "summary": item.get("summary", ""), "source": item.get("publisher", ""), "url": item.get("link", ""), "timestamp": item.get("providerPublishTime")} for item in items[:10]]
                    if ynews:
                        news = ynews
                        ds = "realtime"
        except Exception as e:
            logger.warning("Yahoo News failed: %s — using AI-generated news", e)
    return {"data": news, "updatedAt": datetime.now(timezone.utc).isoformat(), "dataSource": ds}
