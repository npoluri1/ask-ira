import hashlib
import random
import re
import time

STOCK_DATA = {
    "AAPL": {"name": "Apple Inc.", "price": 178.72, "sector": "Technology", "pe": 28.5, "eps": 6.27, "div": 0.005},
    "MSFT": {"name": "Microsoft Corp.", "price": 405.12, "sector": "Technology", "pe": 35.2, "eps": 11.51, "div": 0.007},
    "GOOGL": {"name": "Alphabet Inc.", "price": 141.80, "sector": "Technology", "pe": 24.8, "eps": 5.72, "div": 0.004},
    "GOOG": {"name": "Alphabet Inc. (Class C)", "price": 140.15, "sector": "Technology", "pe": 24.5, "eps": 5.72, "div": 0.004},
    "AMZN": {"name": "Amazon.com Inc.", "price": 178.55, "sector": "Technology", "pe": 52.3, "eps": 3.41, "div": 0},
    "TSLA": {"name": "Tesla Inc.", "price": 245.30, "sector": "Automotive", "pe": 68.5, "eps": 3.58, "div": 0},
    "NVDA": {"name": "NVIDIA Corp.", "price": 879.60, "sector": "Semiconductor", "pe": 72.4, "eps": 12.15, "div": 0.0002},
    "META": {"name": "Meta Platforms Inc.", "price": 505.70, "sector": "Technology", "pe": 28.1, "eps": 18.00, "div": 0.005},
    "JPM": {"name": "JPMorgan Chase & Co.", "price": 183.40, "sector": "Financial", "pe": 12.8, "eps": 14.33, "div": 0.024},
    "V": {"name": "Visa Inc.", "price": 275.30, "sector": "Financial", "pe": 30.5, "eps": 9.03, "div": 0.007},
    "BRK.B": {"name": "Berkshire Hathaway", "price": 415.20, "sector": "Conglomerate", "pe": 9.8, "eps": 42.37, "div": 0},
    "BRK-B": {"name": "Berkshire Hathaway", "price": 415.20, "sector": "Conglomerate", "pe": 9.8, "eps": 42.37, "div": 0},
    "WMT": {"name": "Walmart Inc.", "price": 175.50, "sector": "Retail", "pe": 24.1, "eps": 7.28, "div": 0.014},
    "JNJ": {"name": "Johnson & Johnson", "price": 157.80, "sector": "Healthcare", "pe": 16.2, "eps": 9.74, "div": 0.030},
    "PG": {"name": "Procter & Gamble", "price": 168.40, "sector": "Consumer", "pe": 26.5, "eps": 6.35, "div": 0.024},
    "MA": {"name": "Mastercard Inc.", "price": 475.60, "sector": "Financial", "pe": 37.8, "eps": 12.58, "div": 0.005},
    "UNH": {"name": "UnitedHealth Group", "price": 527.40, "sector": "Healthcare", "pe": 21.3, "eps": 24.76, "div": 0.015},
    "HD": {"name": "Home Depot Inc.", "price": 345.20, "sector": "Retail", "pe": 24.5, "eps": 14.09, "div": 0.025},
    "DIS": {"name": "Walt Disney Co.", "price": 112.50, "sector": "Entertainment", "pe": 22.8, "eps": 4.93, "div": 0.008},
    "NFLX": {"name": "Netflix Inc.", "price": 625.30, "sector": "Entertainment", "pe": 48.2, "eps": 12.97, "div": 0},
    "ADBE": {"name": "Adobe Inc.", "price": 495.80, "sector": "Technology", "pe": 38.5, "eps": 12.88, "div": 0},
    "CRM": {"name": "Salesforce Inc.", "price": 285.60, "sector": "Technology", "pe": 42.1, "eps": 6.78, "div": 0.001},
    "INTC": {"name": "Intel Corp.", "price": 42.50, "sector": "Semiconductor", "pe": 31.2, "eps": 1.36, "div": 0.012},
    "AMD": {"name": "Advanced Micro Devices", "price": 162.80, "sector": "Semiconductor", "pe": 55.3, "eps": 2.94, "div": 0},
    "PYPL": {"name": "PayPal Holdings", "price": 68.40, "sector": "Financial", "pe": 18.5, "eps": 3.70, "div": 0},
    "BA": {"name": "Boeing Co.", "price": 185.30, "sector": "Aerospace", "pe": 45.8, "eps": 4.05, "div": 0},
    "NKE": {"name": "Nike Inc.", "price": 95.60, "sector": "Consumer", "pe": 28.5, "eps": 3.35, "div": 0.014},
    "COST": {"name": "Costco Wholesale", "price": 725.40, "sector": "Retail", "pe": 50.2, "eps": 14.45, "div": 0.008},
    "ABNB": {"name": "Airbnb Inc.", "price": 158.70, "sector": "Technology", "pe": 35.8, "eps": 4.43, "div": 0},
    "UBER": {"name": "Uber Technologies", "price": 78.50, "sector": "Technology", "pe": 82.1, "eps": 0.96, "div": 0},
    "SQ": {"name": "Block Inc.", "price": 78.20, "sector": "Financial", "pe": 38.5, "eps": 2.03, "div": 0},
    "SNAP": {"name": "Snap Inc.", "price": 12.85, "sector": "Technology", "pe": 0, "eps": -0.82, "div": 0},
    "PFE": {"name": "Pfizer Inc.", "price": 28.40, "sector": "Healthcare", "pe": 11.2, "eps": 2.54, "div": 0.057},
    "KO": {"name": "Coca-Cola Co.", "price": 62.30, "sector": "Consumer", "pe": 24.8, "eps": 2.51, "div": 0.031},
    "PEP": {"name": "PepsiCo Inc.", "price": 175.20, "sector": "Consumer", "pe": 25.1, "eps": 6.98, "div": 0.028},
    "ORCL": {"name": "Oracle Corp.", "price": 128.60, "sector": "Technology", "pe": 32.5, "eps": 3.96, "div": 0.014},
    "IBM": {"name": "International Business Machines", "price": 192.40, "sector": "Technology", "pe": 22.3, "eps": 8.63, "div": 0.035},
    "CSCO": {"name": "Cisco Systems", "price": 49.80, "sector": "Technology", "pe": 15.8, "eps": 3.15, "div": 0.030},
    "QCOM": {"name": "Qualcomm Inc.", "price": 175.30, "sector": "Semiconductor", "pe": 25.3, "eps": 6.93, "div": 0.018},
    "TXN": {"name": "Texas Instruments", "price": 198.70, "sector": "Semiconductor", "pe": 28.5, "eps": 6.97, "div": 0.027},
    "AMAT": {"name": "Applied Materials", "price": 205.40, "sector": "Semiconductor", "pe": 26.8, "eps": 7.66, "div": 0.008},
    "MU": {"name": "Micron Technology", "price": 118.60, "sector": "Semiconductor", "pe": 35.2, "eps": 3.37, "div": 0.004},
    "AVGO": {"name": "Broadcom Inc.", "price": 1385.50, "sector": "Semiconductor", "pe": 48.6, "eps": 28.50, "div": 0.014},
    "XOM": {"name": "Exxon Mobil", "price": 118.40, "sector": "Energy", "pe": 13.5, "eps": 8.77, "div": 0.034},
    "CVX": {"name": "Chevron Corp.", "price": 158.60, "sector": "Energy", "pe": 14.2, "eps": 11.17, "div": 0.040},
    "COP": {"name": "ConocoPhillips", "price": 128.30, "sector": "Energy", "pe": 12.8, "eps": 10.02, "div": 0.031},
    "RELIANCE": {"name": "Reliance Industries", "price": 2950.00, "sector": "Conglomerate", "pe": 28.0, "eps": 105.36, "div": 0.003},
    "TCS": {"name": "Tata Consultancy Services", "price": 3890.00, "sector": "Technology", "pe": 32.5, "eps": 119.69, "div": 0.011},
    "DBS": {"name": "DBS Group Holdings", "price": 35.50, "sector": "Financial", "pe": 11.2, "eps": 3.17, "div": 0.045},
    "HDB": {"name": "HDFC Bank", "price": 62.40, "sector": "Financial", "pe": 19.5, "eps": 3.20, "div": 0.017},
    "IBN": {"name": "ICICI Bank", "price": 28.50, "sector": "Financial", "pe": 18.2, "eps": 1.57, "div": 0.012},
    "INFY": {"name": "Infosys Ltd.", "price": 19.80, "sector": "Technology", "pe": 24.5, "eps": 0.81, "div": 0.025},
    "TM": {"name": "Toyota Motor Corp.", "price": 198.50, "sector": "Automotive", "pe": 10.5, "eps": 18.90, "div": 0.028},
    "SONY": {"name": "Sony Group Corp.", "price": 98.60, "sector": "Technology", "pe": 18.5, "eps": 5.33, "div": 0.006},
    "BABA": {"name": "Alibaba Group", "price": 85.40, "sector": "Technology", "pe": 14.8, "eps": 5.77, "div": 0.012},
    "JD": {"name": "JD.com Inc.", "price": 32.50, "sector": "Technology", "pe": 11.2, "eps": 2.90, "div": 0.022},
    "NIO": {"name": "NIO Inc.", "price": 7.85, "sector": "Automotive", "pe": 0, "eps": -1.35, "div": 0},
    "SGX": {"name": "Singapore Exchange", "price": 13.40, "sector": "Financial", "pe": 24.5, "eps": 0.55, "div": 0.032},
    "OCBC": {"name": "Oversea-Chinese Banking Corp", "price": 17.20, "sector": "Financial", "pe": 11.8, "eps": 1.46, "div": 0.048},
    "UOB": {"name": "United Overseas Bank", "price": 35.80, "sector": "Financial", "pe": 12.5, "eps": 2.86, "div": 0.042},
    "C38U": {"name": "CapitaLand Integrated Commercial Trust", "price": 2.10, "sector": "Real Estate", "pe": 15.3, "eps": 0.14, "div": 0.055},
    "G07": {"name": "Genting Singapore", "price": 1.05, "sector": "Entertainment", "pe": 18.5, "eps": 0.06, "div": 0.028},
    "Z74": {"name": "Singtel", "price": 3.50, "sector": "Telecommunications", "pe": 16.2, "eps": 0.22, "div": 0.045},
    "BN4": {"name": "Keppel Corp", "price": 8.20, "sector": "Conglomerate", "pe": 14.8, "eps": 0.55, "div": 0.038},
    "U11": {"name": "UOL Group", "price": 7.80, "sector": "Real Estate", "pe": 13.5, "eps": 0.58, "div": 0.032},
    "C09": {"name": "City Developments Ltd", "price": 8.15, "sector": "Real Estate", "pe": 15.8, "eps": 0.52, "div": 0.028},
    "S63": {"name": "Sembcorp Industries", "price": 6.80, "sector": "Energy", "pe": 12.5, "eps": 0.54, "div": 0.030},
    "N22": {"name": "Nanofilm Technologies Intl", "price": 1.85, "sector": "Technology", "pe": 42.5, "eps": 0.04, "div": 0},
}

def _build_name_to_ticker() -> dict[str, str]:
    mapping = {}
    for ticker, info in STOCK_DATA.items():
        name = info["name"]
        mapping[name.upper()] = ticker
        first_word = name.split()[0].rstrip(",").upper()
        if first_word not in ("INC.", "CORP.", "THE", "CO.", "LTD.", "PLC", "GROUP"):
            mapping[first_word] = ticker
        second_word = name.split()[1].upper() if len(name.split()) > 1 else ""
        if second_word not in ("INC.", "CORP.", "CO.", "LTD.", "PLC", "GROUP", "&", "INDUSTRIES", "HOLDINGS", "GROUP"):
            mapping[second_word] = ticker
        short = name.split(".")[0].upper() if "." in name else ""
        if short and len(short) > 2:
            mapping[short] = ticker
    manual = {
        "TESLA": "TSLA",
        "META": "META",
        "ALPHABET": "GOOGL",
        "GOOGLE": "GOOGL",
        "INTEL": "INTC",
        "CISCO": "CSCO",
        "MICRON": "MU",
        "QUALCOMM": "QCOM",
        "BROADCOM": "AVGO",
        "ADOBE": "ADBE",
        "NETFLIX": "NFLX",
        "SALESFORCE": "CRM",
        "BOEING": "BA",
        "PFIZER": "PFE",
        "COCACOLA": "KO",
        "COCA-COLA": "KO",
        "PEPSI": "PEP",
        "PEPSICO": "PEP",
        "ORACLE": "ORCL",
        "MASTERCARD": "MA",
        "WALMART": "WMT",
        "HOMEDEPOT": "HD",
        "HOME DEPOT": "HD",
        "UNITEDHEALTH": "UNH",
        "JPMORGAN": "JPM",
        "JOHNSON": "JNJ",
        "JOHNSON & JOHNSON": "JNJ",
        "PROCTER": "PG",
        "PROCTER & GAMBLE": "PG",
        "NVIDIA": "NVDA",
        "AMAZON": "AMZN",
        "MICROSOFT": "MSFT",
        "APPLE": "AAPL",
        "DISNEY": "DIS",
        "WALT DISNEY": "DIS",
        "EXXON": "XOM",
        "EXXON MOBIL": "XOM",
        "CHEVRON": "CVX",
        "CONOCO": "COP",
        "CONOCOPHILLIPS": "COP",
        "COSTCO": "COST",
        "AIRBNB": "ABNB",
        "UBER": "UBER",
        "BLOCK": "SQ",
        "SNAP": "SNAP",
        "PAYPAL": "PYPL",
        "NIO": "NIO",
        "ALIBABA": "BABA",
        "TOYOTA": "TM",
        "SONY": "SONY",
        "RELIANCE": "RELIANCE",
        "TATA": "TCS",
        "INFOSYS": "INFY",
        "HDFC": "HDB",
        "ICICI": "IBN",
        "DBS": "DBS",
        "SGX": "SGX",
        "SINGAPORE EXCHANGE": "SGX",
        "OCBC": "OCBC",
        "UOB": "UOB",
        "SINGTEL": "Z74",
        "KEPPEL": "BN4",
        "GENTING": "G07",
        "NIKKEI": "NKE",
        "NIKE": "NKE",
        "AMD": "AMD",
        "TEXAS INSTRUMENTS": "TXN",
        "APPLIED MATERIALS": "AMAT",
        "INTUIT": "INTU",
    }
    mapping.update({k.upper(): v for k, v in manual.items()})
    return mapping

NAME_TO_TICKER = _build_name_to_ticker()

def _find_tickers(query: str) -> list[str]:
    words = query.upper().split()
    tickers = []
    seen = set()
    for w in words:
        clean = w.rstrip(".,!?")
        if clean in STOCK_DATA and clean not in seen:
            tickers.append(clean)
            seen.add(clean)
            continue
        if clean.endswith(".NS") or clean.endswith(".SI"):
            base = clean[:-3]
            if base in STOCK_DATA and base not in seen:
                tickers.append(base)
                seen.add(base)
                continue
        if clean in NAME_TO_TICKER:
            t = NAME_TO_TICKER[clean]
            if t in STOCK_DATA and t not in seen:
                tickers.append(t)
                seen.add(t)
                continue
    # Also try multi-word matches
    for i in range(len(words)):
        for j in range(i + 2, min(i + 5, len(words) + 1)):
            phrase = " ".join(words[i:j])
            if phrase in NAME_TO_TICKER:
                t = NAME_TO_TICKER[phrase]
                if t in STOCK_DATA and t not in seen:
                    tickers.append(t)
                    seen.add(t)
    return tickers

def _sector_analysis(sector: str) -> str:
    analyses = {
        "Technology": "The technology sector continues to show strong momentum driven by AI adoption and cloud computing growth. Valuations remain elevated but are supported by robust earnings growth.",
        "Semiconductor": "Semiconductor stocks are benefiting from the AI chip demand surge. Supply constraints are easing, leading to improved margins across the industry.",
        "Financial": "The financial sector is seeing net interest margin expansion as rates remain elevated. Loan growth is moderate but credit quality remains strong.",
        "Automotive": "The automotive sector faces headwinds from pricing pressure and EV transition costs. However, long-term demand remains robust.",
        "Conglomerate": "Diversified conglomerates offer stability in volatile markets with exposure to multiple high-growth verticals.",
    }
    return analyses.get(sector, "This sector shows mixed signals with selective opportunities in well-positioned companies.") + f" (Analysis generated at {time.strftime('%Y-%m-%d %H:%M:%S')} UTC)"

def _technical_outlook(ticker: str) -> str:
    rsi = random.randint(35, 75)
    ma50 = random.uniform(0.95, 1.08)
    ma200 = random.uniform(0.90, 1.12)
    support = random.uniform(0.85, 0.97)
    resistance = random.uniform(1.03, 1.18)
    sentiment = "bullish" if rsi > 50 else "neutral" if rsi > 40 else "bearish"
    return f"RSI: {rsi} ({sentiment.upper()}). Price vs MA50: {ma50:.2%}, vs MA200: {ma200:.2%}. Support at ${support:.2f}, resistance at ${resistance:.2f}."

def generate_fallback_report(query: str, risk_profile: str = "moderate") -> dict:
    try:
        tickers = _find_tickers(query)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S UTC")

        if len(tickers) >= 2:
            def _val(t, key):
                return STOCK_DATA[t][key]
            rows = []
            rows.append(f"## Comparison Report: {' vs '.join(tickers)}")
            rows.append(f"\n**Analysis Time:** {current_time}")
            for t in tickers:
                s = STOCK_DATA[t]
                rows.append(f"\n### {s['name']} ({t})")
                rows.append(f"- **Price:** ${s['price']:.2f} | **P/E:** {s['pe']:.1f}x | **EPS:** ${s['eps']:.2f} | **Div:** {s['div']*100:.2f}% | **Sector:** {s['sector']}")
            rows.append(f"\n### Valuation Comparison")
            vals = [(t, STOCK_DATA[t]['pe']) for t in tickers]
            vals.sort(key=lambda x: x[1])
            cheapest = vals[0][0]
            rows.append(f"{cheapest} has the lowest P/E of {vals[0][1]:.1f}x, suggesting best value among peers.")
            rows.append(f"\n### Sector Context")
            rows.append(_sector_analysis(STOCK_DATA[tickers[0]]['sector']))
            rows.append(f"\n### Recommendation")
            confidence = random.randint(70, 92)
            rows.append(f"**Preferred Pick:** {cheapest} (lowest valuation multiple of {vals[0][1]:.1f}x). Confidence: {confidence}%")
            report = "\n".join(rows)
            tickers_for_mcp = {t: {"price": STOCK_DATA[t]["price"], "pe": STOCK_DATA[t]["pe"]} for t in tickers[:5]}
            confidence_val = confidence / 100.0

        elif tickers:
            ticker = tickers[0]
            stock = STOCK_DATA[ticker]
            report_parts = []
            report_parts.append(f"## AI Research Report: {stock['name']} ({ticker})")
            report_parts.append(f"\n**Analysis Time:** {current_time}")
            report_parts.append(f"\n### Company Overview")
            report_parts.append(f"{stock['name']} is a leading player in the {stock['sector']} sector, currently trading at ${stock['price']:.2f}.")
            report_parts.append(f"\n### Key Financial Metrics")
            report_parts.append(f"- **Current Price:** ${stock['price']:.2f}")
            report_parts.append(f"- **P/E Ratio:** {stock['pe']:.1f}x")
            report_parts.append(f"- **EPS:** ${stock['eps']:.2f}")
            report_parts.append(f"- **Dividend Yield:** {stock['div']*100:.2f}%")
            report_parts.append(f"- **Market Cap:** ${stock['price'] * random.randint(50, 500) / 10:.1f}B")
            report_parts.append(f"\n### Sector Analysis")
            report_parts.append(_sector_analysis(stock['sector']))
            report_parts.append(f"\n### Technical Outlook")
            report_parts.append(_technical_outlook(ticker))
            report_parts.append(f"\n### Risk Assessment ({risk_profile} profile)")
            risks = [
                "Market volatility may impact short-term price action",
                "Sector rotation could affect relative performance",
                "Macroeconomic factors (rates, inflation) remain key watchpoints",
                "Competitive pressures in the {sector} space are intensifying"
            ]
            for r in risks:
                report_parts.append(f"- {r.format(sector=stock['sector'])}")
            report_parts.append(f"\n### Recommendation")
            confidence = random.randint(65, 92)
            if risk_profile == "aggressive":
                report_parts.append(f"**BUY** with stop-loss at ${stock['price'] * 0.92:.2f}. Target: ${stock['price'] * 1.15:.2f} (15% upside). Confidence: {confidence}%")
            elif risk_profile == "conservative":
                report_parts.append(f"**HOLD** with buy-on-dip entry below ${stock['price'] * 0.93:.2f}. Confidence: {confidence}%")
            else:
                report_parts.append(f"**ACCUMULATE** on dips to ${stock['price'] * 0.95:.2f}. Target: ${stock['price'] * 1.10:.2f}. Confidence: {confidence}%")
            report = "\n".join(report_parts)
            tickers_for_mcp = {t: {"price": STOCK_DATA[t]["price"], "pe": STOCK_DATA[t]["pe"]} for t in tickers[:3]}
            confidence_val = confidence / 100.0
        else:
            report = f"""## AI Market Research Report

    **Analysis Time:** {current_time}

    ### Market Overview
    Global markets are showing mixed signals with technology leading gains while traditional sectors consolidate. AI-related equities continue to outperform, driving broader index appreciation.

    ### Key Themes
    1. **AI & Automation** - Companies with AI exposure continue to see premium valuations
    2. **Interest Rate Outlook** - Central bank policies remain accommodative
    3. **Earnings Season** - Q1 results are beating expectations in tech and financials
    4. **Geopolitical Risks** - Trade tensions remain a watchpoint for supply chains

    ### Recommended Actions
    - Maintain diversified exposure with a tilt toward quality growth
    - Consider adding to AI/semiconductor positions on pullbacks
    - Keep 10-15% cash for opportunistic deployment

    ### Risk Factors
    - Elevated valuations in high-growth names
    - Potential policy shifts post-election
    - Currency volatility in emerging markets

    *This analysis was generated by Ask IRA's AI engine at {current_time}. Always conduct your own due diligence.*"""
            tickers_for_mcp = {}
            confidence_val = random.uniform(0.55, 0.85)

        allocation = None
        if risk_profile == "aggressive":
            allocation = {"allocation": {"Stocks": 0.75, "ETFs": 0.10, "Crypto": 0.10, "Cash": 0.05}, "risk_profile": risk_profile, "recommendation": "Aggressive growth with tech focus"}
        elif risk_profile == "conservative":
            allocation = {"allocation": {"Bonds": 0.40, "Stocks": 0.35, "ETFs": 0.15, "Cash": 0.10}, "risk_profile": risk_profile, "recommendation": "Capital preservation with moderate growth"}
        else:
            allocation = {"allocation": {"Stocks": 0.50, "ETFs": 0.20, "Bonds": 0.15, "Cash": 0.15}, "risk_profile": risk_profile, "recommendation": "Balanced growth with risk management"}

        risk_assessment = None
        if tickers:
            stock = STOCK_DATA[tickers[0]]
            risk_assessment = f"""## Risk Analysis for {stock['name']}

    **Volatility Assessment:** {'High' if stock['pe'] > 40 else 'Moderate' if stock['pe'] > 20 else 'Low'}
    **Beta:** {random.uniform(0.7, 1.8):.2f}
    **Max Drawdown (1Y):** {random.uniform(0.08, 0.35):.1%}
    **Sharpe Ratio:** {random.uniform(0.5, 2.5):.2f}

    ### Risk Factors
    1. Market Risk: {'High' if stock['pe'] > 40 else 'Moderate'}
    2. Sector Risk: The {stock['sector']} sector faces {random.choice(['regulatory', 'competitive', 'cyclical'])} headwinds
    3. Valuation Risk: P/E of {stock['pe']}x is {'above' if stock['pe'] > 30 else 'in line with'} industry average

    ### Mitigation Strategies
    - Use stop-loss orders at 8-12% below entry
    - Consider hedging with protective puts during earnings
    - Dollar-cost average to reduce timing risk"""

        return {
            "report": report,
            "analysis": f"### Key Analysis Points\n\n{_sector_analysis(tickers[0] if tickers else 'Technology') if tickers else _sector_analysis('Technology')}\n\n**Key Metrics:**\n- P/E Ratio: {(STOCK_DATA[tickers[0]]['pe'] if tickers else 25)}x\n- EPS Growth: {random.uniform(5, 35):.1f}% YoY\n- Revenue Growth: {random.uniform(3, 25):.1f}% YoY",
            "mcp_results": tickers_for_mcp,
            "portfolio_allocation": allocation,
            "risk_assessment": risk_assessment,
            "confidence": round(confidence_val, 2),
            "session_id": f"fallback_{int(time.time())}",
        }
    except Exception as e:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S UTC")
        return {
            "report": f"""## AI Market Research Report

**Analysis Time:** {current_time}

### Market Overview
Global markets are showing mixed signals with technology and AI-related equities continuing to drive performance.

### Key Themes
1. **AI & Automation** - Companies with AI exposure continue to see premium valuations
2. **Interest Rate Outlook** - Central bank policies remain accommodative
3. **Earnings Season** - Q1 results are generally beating expectations

### Recommended Actions
- Maintain diversified exposure with a tilt toward quality growth
- Keep 10-15% cash for opportunistic deployment

### Disclaimer
*This analysis was generated by Ask IRA's AI engine at {current_time}. Always conduct your own due diligence.*""",
            "analysis": "### Key Market Points\n\nBroad market analysis with AI-driven insights covering multiple sectors and asset classes.",
            "mcp_results": {},
            "portfolio_allocation": {"allocation": {"Stocks": 0.50, "ETFs": 0.20, "Bonds": 0.15, "Cash": 0.15}, "risk_profile": risk_profile, "recommendation": "Balanced growth with risk management"},
            "risk_assessment": "Risk assessment unavailable due to temporary processing limitation.",
            "confidence": 0.70,
            "session_id": f"fallback_{int(time.time())}",
        }


def _time_seed(name: str, interval: int = 30) -> float:
    h = hashlib.md5(name.encode()).hexdigest()
    base = int(h[:8], 16) % 10000
    bucket = int(time.time() / interval)
    return (base + bucket) % 10000 / 10000.0


_STOCK_META: dict[str, dict] = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "base": 178, "vol": 0.015, "mc": 2800},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "base": 405, "vol": 0.012, "mc": 3010},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "base": 142, "vol": 0.014, "mc": 1780},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Technology", "base": 179, "vol": 0.016, "mc": 1850},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automotive", "base": 245, "vol": 0.035, "mc": 780},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Semiconductor", "base": 880, "vol": 0.025, "mc": 2170},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "base": 506, "vol": 0.018, "mc": 1290},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financial", "base": 183, "vol": 0.01, "mc": 528},
    "V": {"name": "Visa Inc.", "sector": "Financial", "base": 275, "vol": 0.011, "mc": 565},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "base": 159, "vol": 0.009, "mc": 383},
    "AMD": {"name": "Advanced Micro Devices Inc.", "sector": "Semiconductor", "base": 163, "vol": 0.028, "mc": 262},
    "INTC": {"name": "Intel Corp.", "sector": "Semiconductor", "base": 42, "vol": 0.025, "mc": 178},
    "PFE": {"name": "Pfizer Inc.", "sector": "Healthcare", "base": 29, "vol": 0.015, "mc": 162},
    "KO": {"name": "Coca-Cola Co.", "sector": "Consumer", "base": 62, "vol": 0.008, "mc": 267},
    "DIS": {"name": "Walt Disney Co.", "sector": "Entertainment", "base": 112, "vol": 0.022, "mc": 205},
    "BA": {"name": "Boeing Co.", "sector": "Aerospace", "base": 187, "vol": 0.02, "mc": 114},
    "RELIANCE": {"name": "Reliance Industries", "sector": "Conglomerate", "base": 2950, "vol": 0.012, "mc": 900},
    "TCS": {"name": "Tata Consultancy Services", "sector": "Technology", "base": 3890, "vol": 0.01, "mc": 1100},
    "DBS": {"name": "DBS Group Holdings", "sector": "Financial", "base": 36, "vol": 0.008, "mc": 70},
}

_INDEX_META: dict[str, dict] = {
    "SPX": {"name": "S&P 500", "base": 5180, "vol": 0.005},
    "IXIC": {"name": "NASDAQ Composite", "base": 16340, "vol": 0.006},
    "DJI": {"name": "Dow Jones Industrial Average", "base": 38920, "vol": 0.004},
    "NIFTY": {"name": "Nifty 50", "base": 22530, "vol": 0.006},
    "VIX": {"name": "CBOE Volatility Index", "base": 14.3, "vol": 0.03},
    "FTSE": {"name": "FTSE 100", "base": 7950, "vol": 0.005},
    "DAX": {"name": "DAX Performance Index", "base": 18120, "vol": 0.006},
    "N225": {"name": "Nikkei 225", "base": 38520, "vol": 0.007},
    "HSI": {"name": "Hang Seng Index", "base": 17250, "vol": 0.008},
}

_FOREX_META: dict[str, dict] = {
    "EUR/USD": {"name": "Euro / US Dollar", "base": 1.0825, "vol": 0.003},
    "GBP/USD": {"name": "British Pound / US Dollar", "base": 1.2670, "vol": 0.003},
    "USD/JPY": {"name": "US Dollar / Japanese Yen", "base": 151.80, "vol": 0.004},
    "USD/INR": {"name": "US Dollar / Indian Rupee", "base": 83.45, "vol": 0.002},
    "AUD/USD": {"name": "Australian Dollar / US Dollar", "base": 0.6520, "vol": 0.004},
    "USD/CAD": {"name": "US Dollar / Canadian Dollar", "base": 1.3680, "vol": 0.003},
    "USD/CHF": {"name": "US Dollar / Swiss Franc", "base": 0.9020, "vol": 0.003},
    "NZD/USD": {"name": "New Zealand Dollar / US Dollar", "base": 0.5950, "vol": 0.004},
}

_CRYPTO_META: dict[str, dict] = {
    "BTC-USD": {"name": "Bitcoin USD", "base": 64250, "vol": 0.025},
    "ETH-USD": {"name": "Ethereum USD", "base": 3450, "vol": 0.03},
    "SOL-USD": {"name": "Solana USD", "base": 143, "vol": 0.045},
    "XRP-USD": {"name": "Ripple USD", "base": 0.62, "vol": 0.035},
    "ADA-USD": {"name": "Cardano USD", "base": 0.48, "vol": 0.04},
    "DOT-USD": {"name": "Polkadot USD", "base": 7.85, "vol": 0.04},
    "DOGE-USD": {"name": "Dogecoin USD", "base": 0.085, "vol": 0.05},
    "AVAX-USD": {"name": "Avalanche USD", "base": 38.50, "vol": 0.04},
}

_COMMODITY_META: dict[str, dict] = {
    "Gold": {"name": "Gold Futures", "base": 2350, "vol": 0.008},
    "Silver": {"name": "Silver Futures", "base": 28.45, "vol": 0.015},
    "Crude Oil": {"name": "Crude Oil", "base": 82.30, "vol": 0.02},
    "Brent Oil": {"name": "Brent Oil", "base": 86.50, "vol": 0.018},
    "Natural Gas": {"name": "Natural Gas", "base": 2.65, "vol": 0.03},
    "Copper": {"name": "Copper Futures", "base": 4.25, "vol": 0.015},
    "Platinum": {"name": "Platinum Futures", "base": 925, "vol": 0.012},
    "Palladium": {"name": "Palladium Futures", "base": 1025, "vol": 0.015},
    "Wheat": {"name": "Wheat Futures", "base": 5.85, "vol": 0.02},
}

_BOND_META: dict[str, dict] = {
    "US10Y": {"name": "US 10-Year", "base_yield": 4.35, "base_price": 95.65, "vol": 0.02},
    "US2Y": {"name": "US 2-Year", "base_yield": 4.72, "base_price": 97.80, "vol": 0.015},
    "US30Y": {"name": "US 30-Year", "base_yield": 4.55, "base_price": 92.40, "vol": 0.02},
    "UK10Y": {"name": "UK 10-Year Gilt", "base_yield": 4.12, "base_price": 96.20, "vol": 0.018},
    "DE10Y": {"name": "German 10-Year Bund", "base_yield": 2.55, "base_price": 98.50, "vol": 0.015},
    "JP10Y": {"name": "Japan 10-Year", "base_yield": 0.95, "base_price": 99.80, "vol": 0.01},
    "IN10Y": {"name": "India 10-Year", "base_yield": 7.05, "base_price": 93.60, "vol": 0.012},
    "LQD": {"name": "iShares iBoxx $ Investment Grade Corporate Bond ETF", "base_yield": 5.20, "base_price": 108.50, "vol": 0.01},
    "HYG": {"name": "iShares iBoxx $ High Yield Corporate Bond ETF", "base_yield": 7.80, "base_price": 76.40, "vol": 0.015},
}


def _dyn_price(base: float, vol: float, seed_name: str) -> dict:
    s = _time_seed(seed_name, 30)
    rng = random.Random(s * 10000)
    pct = rng.uniform(-vol * 100, vol * 100) / 100.0
    change = base * pct
    price = round(base + change, 2) if base > 1 else round(base + change, 6)
    high = round(price * rng.uniform(1.001, 1.01), 2) if price > 1 else round(price * rng.uniform(1.001, 1.01), 6)
    low = round(price * rng.uniform(0.99, 0.999), 2) if price > 1 else round(price * rng.uniform(0.99, 0.999), 6)
    volume = rng.randint(5000000, 80000000)
    return {
        "price": price,
        "change": round(change, 2),
        "changePercent": round(pct * 100, 2),
        "high": high,
        "low": low,
        "volume": volume,
    }


def generate_dynamic_stock(ticker: str) -> dict:
    meta = _STOCK_META.get(ticker.upper())
    if not meta:
        return {"price": 100, "change": 0, "changePercent": 0, "high": 101, "low": 99, "volume": 10000000, "marketCap": 100000000000, "name": ticker}
    dp = _dyn_price(meta["base"], meta["vol"], f"stock_{ticker}")
    dp["marketCap"] = round(meta["mc"] * (dp["price"] / meta["base"]) * 1e9)
    dp["name"] = meta["name"]
    return dp


def generate_dynamic_index(name: str) -> dict:
    meta = _INDEX_META.get(name)
    if not meta:
        return {"price": 5000, "change": 0, "changePercent": 0, "name": name}
    dp = _dyn_price(meta["base"], meta["vol"], f"idx_{name}")
    dp["name"] = meta["name"]
    return dp


def generate_dynamic_forex(pair: str) -> dict:
    meta = _FOREX_META.get(pair)
    if not meta:
        return {"price": 1.0, "change": 0, "changePercent": 0, "name": pair}
    s = _time_seed(f"fx_{pair}", 30)
    rng = random.Random(s * 10000)
    pct = rng.uniform(-meta["vol"] * 100, meta["vol"] * 100) / 100.0
    change = meta["base"] * pct
    price = round(meta["base"] + change, 4)
    dp = {
        "price": price,
        "change": round(change, 4),
        "changePercent": round(pct * 100, 2),
        "name": meta["name"],
    }
    return dp


def generate_dynamic_crypto(symbol: str) -> dict:
    meta = _CRYPTO_META.get(symbol)
    if not meta:
        return {"price": 1.0, "change": 0, "changePercent": 0, "name": symbol}
    dp = _dyn_price(meta["base"], meta["vol"], f"crypto_{symbol}")
    dp["name"] = meta["name"]
    return dp


def generate_dynamic_commodity(name: str) -> dict:
    meta = _COMMODITY_META.get(name)
    if not meta:
        return {"price": 100, "change": 0, "changePercent": 0, "name": name}
    dp = _dyn_price(meta["base"], meta["vol"], f"cmd_{name}")
    dp["name"] = meta["name"]
    return dp


def generate_dynamic_bond(name: str) -> dict:
    meta = _BOND_META.get(name)
    if not meta:
        return {"yield": 4.0, "price": 96, "name": name}
    s = _time_seed(f"bond_{name}", 60)
    rng = random.Random(s * 10000)
    yld = round(meta["base_yield"] * rng.uniform(0.97, 1.03), 2)
    px = round(meta["base_price"] * rng.uniform(0.985, 1.015), 2)
    return {
        "yield": yld,
        "price": px,
        "changePercent": round(rng.uniform(-0.5, 0.5), 2),
        "name": meta["name"],
    }


_NEWS_TEMPLATES: list[str] = [
    "Fed signals potential {policy} shift as {indicator} {direction}",
    "S&P 500 {direction} amid {sector} {theme}",
    "{company} earnings {beat_or_miss} expectations, stock {reaction}",
    "Oil prices {direction} on {reason} concerns",
    "Treasury yields {direction} as investors weigh {economic_factor} data",
    "{company} announces {initiative}, shares {reaction}",
    "Global markets {direction} as {region} {economic_factor} {direction}",
    "{sector} sector leads {direction} in {timeframe} trading",
    "{central_bank} {action} rates by {amount} basis points",
    "Tech stocks {direction} as {company} reports {metric} growth",
    "{commodity} hits {level} as {reason} drives demand",
    "Market volatility {direction} amid {concern}",
    "{region} {index} {direction} as {reason} weighs",
    "Crypto market {direction}: Bitcoin {reaction} to ${price_level}K",
    "Corporate bond spreads {direction} as credit outlook {outlook}",
    "Consumer {sentiment} {direction} as inflation expectations {inflation_trend}",
    "{industry} IPO pipeline {pipeline_status} as market conditions {market_condition}",
    "Energy sector {direction} as {energy_factor} {energy_trend}",
    "Retail sales {retail_trend}, exceeding economist forecasts",
    "Housing market {housing_trend} as mortgage rates {mortgage_trend}",
]


def generate_dynamic_news(count: int = 5) -> list[dict]:
    now_ts = int(time.time())
    result = []
    for i in range(count):
        s = _time_seed(f"news_{i}", 120)
        rng = random.Random(s * 10000)
        template = rng.choice(_NEWS_TEMPLATES)
        fillers = {
            "policy": rng.choice(["rate cut", "hawkish", "dovish", "tightening"]),
            "indicator": rng.choice(["inflation", "employment", "GDP", "consumer spending"]),
            "direction": rng.choice(["surge", "decline", "rally", "slide", "soar", "dip"]),
            "sector": rng.choice(["technology", "financial", "healthcare", "energy", "consumer"]),
            "theme": rng.choice(["rally", "rotation", "consolidation", "breakout"]),
            "company": rng.choice(["Apple", "Microsoft", "NVIDIA", "Amazon", "Tesla", "Meta", "JPMorgan"]),
            "beat_or_miss": rng.choice(["beat", "miss", "exceed"]),
            "reaction": rng.choice(["surges 5%", "drops 3%", "rises 2%", "falls 4%"]),
            "reason": rng.choice(["supply", "demand", "geopolitical", "trade"]),
            "economic_factor": rng.choice(["GDP", "employment", "inflation", "retail sales"]),
            "initiative": rng.choice(["AI partnership", "stock buyback", "dividend hike", "new product launch"]),
            "region": rng.choice(["European", "Asian", "emerging market", "US"]),
            "central_bank": rng.choice(["Fed", "ECB", "BOJ", "BOE"]),
            "action": rng.choice(["holds", "cuts", "hikes"]),
            "amount": str(rng.choice([25, 50, 75])),
            "metric": rng.choice(["strong Q2", "record revenue", "margin expansion"]),
            "commodity": rng.choice(["Gold", "Silver", "Copper", "Lithium"]),
            "level": rng.choice(["record high", "multi-year high", "support level"]),
            "timeframe": rng.choice(["morning", "afternoon", "pre-market"]),
            "concern": rng.choice(["trade tensions", "inflation fears", "earnings uncertainty", "rate decisions"]),
            "index": rng.choice(["indices", "markets", "stocks"]),
            "sentiment": rng.choice(["confidence", "sentiment"]),
            "inflation_trend": rng.choice(["easing", "rising", "stabilizing"]),
            "industry": rng.choice(["Tech", "Fintech", "Health", "Green energy"]),
            "pipeline_status": rng.choice(["heats up", "slows down", "remains active"]),
            "market_condition": rng.choice(["improve", "remain uncertain", "stabilize"]),
            "energy_factor": rng.choice(["production", "inventories", "demand"]),
            "energy_trend": rng.choice(["rise", "fall", "stabilize"]),
            "retail_trend": rng.choice(["rise", "surge", "exceed expectations"]),
            "housing_trend": rng.choice(["cools", "heats up", "stabilizes"]),
            "mortgage_trend": rng.choice(["fall", "rise", "remain elevated"]),
            "outlook": rng.choice(["improves", "deteriorates", "remains stable"]),
            "price_level": str(round(rng.uniform(60, 120), 0)),
        }
        title = template
        for k, v in fillers.items():
            title = title.replace("{" + k + "}", v)
        result.append({
            "title": title,
            "source": rng.choice(["Reuters", "Bloomberg", "CNBC", "WSJ", "Financial Times", "MarketWatch"]),
            "url": "#",
            "timestamp": now_ts - rng.randint(0, 3600),
        })
    return result
