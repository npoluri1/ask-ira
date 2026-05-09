"""Seed the vector store with sample financial documents for RAG."""

import asyncio
from pathlib import Path

from langchain_core.documents import Document

from data.loader import load_company_descriptions
from src.config import get_settings
from src.rag.vector_store import VectorStore


def _build_seed_docs() -> list[Document]:
    docs = []
    for entry in load_company_descriptions():
        ticker = entry.get("ticker", "")
        if ticker:
            docs.append(Document(
                page_content=f"{ticker}: {entry['content']}",
                metadata={"source": entry.get("source", "company_overview"), "ticker": ticker, "sector": entry.get("sector", "Technology")},
            ))
        elif entry.get("topic"):
            docs.append(Document(
                page_content=entry["content"],
                metadata={"source": entry.get("source", "framework"), "topic": entry["topic"]},
            ))
    return docs


async def main():
    settings = get_settings()
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    seed_docs = _build_seed_docs()
    store = VectorStore()
    store.add_documents(seed_docs)

    tickers = list({d.metadata.get("ticker", "") for d in seed_docs if d.metadata.get("ticker")})
    topics = list({d.metadata.get("topic", "") for d in seed_docs if d.metadata.get("topic")})
    print(f"Seeded {len(seed_docs)} documents into ChromaDB at {persist_dir}")
    print(f"Tickers: {', '.join(sorted(tickers))}")
    print(f"Topics: {', '.join(sorted(topics))}")


def entry_point():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
