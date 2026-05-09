import json
import csv
import os
from pathlib import Path
from typing import Any, Optional

DATA_DIR = Path(__file__).parent.resolve()


def load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_text(filename: str) -> str:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_companies() -> list[dict]:
    return load_json("companies.json")


def load_people() -> list[dict]:
    return load_json("people.json")


def load_financial_metrics() -> list[dict]:
    return load_json("financial_metrics.json")


def load_financial_metrics_for_ticker(ticker: str) -> Optional[dict]:
    metrics = load_financial_metrics()
    for m in metrics:
        if m["ticker"].upper() == ticker.upper():
            return m
    return None


def load_news_articles(ticker: Optional[str] = None) -> list[dict]:
    articles = load_json("news_articles.json")
    if ticker:
        return [a for a in articles if a["ticker"].upper() == ticker.upper()]
    return articles


def load_macro_indicators() -> dict:
    return load_json("macro_indicators.json")


def load_sentiment_lexicon() -> dict:
    return load_json("sentiment_lexicon.json")


def load_knowledge_base(topic: Optional[str] = None) -> list[dict]:
    articles = load_json("knowledge_base.json")
    if topic:
        return [a for a in articles if a["topic"] == topic]
    return articles


def load_knowledge_base_by_id(kb_id: str) -> Optional[dict]:
    articles = load_knowledge_base()
    for a in articles:
        if a["id"] == kb_id:
            return a
    return None


def load_company_descriptions(ticker: Optional[str] = None) -> list[dict]:
    descriptions = load_json("company_descriptions.json")
    if ticker:
        return [d for d in descriptions if d.get("ticker", "").upper() == ticker.upper()]
    return descriptions


def load_eval_queries(category: Optional[str] = None) -> list[dict]:
    queries = load_json("eval_queries.json")
    if category:
        return [q for q in queries if q["category"] == category]
    return queries


def load_sec_filings(ticker: Optional[str] = None) -> list[dict]:
    filings = load_json("sec_filings.json")
    if ticker:
        return [f for f in filings if f["ticker"].upper() == ticker.upper()]
    return filings


def load_sample_report(ticker: str) -> Optional[str]:
    ticker_lower = ticker.lower()
    for fname in ["report_macro.md", "report_esg_aapl.md"]:
        path = DATA_DIR / "sample_reports" / fname
        if path.exists():
            return load_text(str(path.relative_to(DATA_DIR)))
    path = DATA_DIR / "sample_reports" / f"report_{ticker_lower}.md"
    if path.exists():
        return load_text(str(path.relative_to(DATA_DIR)))
    return None


def load_all_seed_data() -> dict:
    return {
        "companies": load_companies(),
        "people": load_people(),
        "financial_metrics": load_financial_metrics(),
        "news_articles": load_news_articles(),
        "macro_indicators": load_macro_indicators(),
        "sentiment_lexicon": load_sentiment_lexicon(),
        "knowledge_base": load_knowledge_base(),
        "company_descriptions": load_company_descriptions(),
        "eval_queries": load_eval_queries(),
        "sec_filings": load_sec_filings(),
    }
