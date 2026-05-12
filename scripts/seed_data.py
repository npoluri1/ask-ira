"""Seed data loader and ChromaDB initializer for Ask IRA.

Populates the vector store from JSON seed data files.
Usage: python -m scripts.seed_data
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.documents import Document

from data.loader import (
    load_companies,
    load_company_descriptions,
    load_financial_metrics,
    load_knowledge_base,
    load_macro_indicators,
    load_news_articles,
    load_sec_filings,
    load_sentiment_lexicon,
)
from src.config.logging import setup_logging
from src.rag.vector_store import VectorStore

logger = setup_logging()


def build_documents() -> list[Document]:
    docs: list[Document] = []

    for c in load_companies():
        docs.append(Document(
            page_content=f"{c['name']} ({c['ticker']}): {c.get('sector', '')} - {c.get('description', '')}",
            metadata={"source": "companies", "ticker": c["ticker"]},
        ))

    for d in load_company_descriptions():
        docs.append(Document(
            page_content=f"{d.get('ticker', '')}: {d.get('description', '')}",
            metadata={"source": "company_descriptions", "ticker": d.get("ticker", "")},
        ))

    for m in load_financial_metrics():
        docs.append(Document(
            page_content=(
                f"{m['ticker']} - Revenue: ${m['revenue']:,.0f}, "
                f"Net Income: ${m['net_income']:,.0f}, "
                f"EPS: ${m['eps']:.2f}, P/E: {m['pe_ratio']:.1f}"
            ),
            metadata={"source": "financial_metrics", "ticker": m["ticker"]},
        ))

    for a in load_news_articles():
        docs.append(Document(
            page_content=f"{a['title']}: {a.get('summary', a.get('content', ''))}",
            metadata={"source": "news", "ticker": a.get("ticker", ""), "date": a.get("date", "")},
        ))

    for kb in load_knowledge_base():
        docs.append(Document(
            page_content=f"{kb['title']}: {kb['content']}",
            metadata={"source": "knowledge_base", "topic": kb.get("topic", ""), "id": kb.get("id", "")},
        ))

    mi = load_macro_indicators()
    for section, data in mi.items():
        docs.append(Document(
            page_content=f"{section}: {data}",
            metadata={"source": "macro", "indicator": section},
        ))

    for f in load_sec_filings():
        for filing in f.get("filings", []):
            docs.append(Document(
                page_content=f"{f['ticker']} {filing.get('type', '')} filing: {filing.get('description', '')}",
                metadata={"source": "sec_filing", "ticker": f["ticker"]},
            ))

    lex = load_sentiment_lexicon()
    positive = lex.get("positive_words", [])
    negative = lex.get("negative_words", [])
    docs.append(Document(
        page_content=f"Positive sentiment words: {', '.join(positive[:50])}",
        metadata={"source": "sentiment_lexicon", "type": "positive"},
    ))
    docs.append(Document(
        page_content=f"Negative sentiment words: {', '.join(negative[:50])}",
        metadata={"source": "sentiment_lexicon", "type": "negative"},
    ))

    return docs


def seed_vector_store(vs: VectorStore, docs: list[Document], clear_first: bool = True) -> int:
    if clear_first:
        try:
            vs.store.delete_collection()
        except Exception:
            pass
        from langchain_chroma import Chroma
        from src.rag.embeddings import get_embedding_model
        vs.store = Chroma(
            collection_name="ask_ira_docs",
            embedding_function=get_embedding_model(),
        )
    vs.add_documents(docs)
    return len(docs)


def entry_point():
    parser = argparse.ArgumentParser(description="Seed Ask IRA data")
    parser.add_argument("--clear", action="store_true", default=True, help="Clear existing data before seeding")
    parser.add_argument("--no-clear", action="store_false", dest="clear", help="Append to existing data")
    args = parser.parse_args()

    logger.info("Building documents from seed data...")
    docs = build_documents()
    logger.info("Built %d documents", len(docs))

    logger.info("Initializing vector store...")
    vs = VectorStore()
    count = seed_vector_store(vs, docs, clear_first=args.clear)
    logger.info("Seeded %d documents into ChromaDB", count)


if __name__ == "__main__":
    entry_point()
