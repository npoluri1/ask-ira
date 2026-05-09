from typing import Protocol

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from src.rag.vector_store import VectorStore


class Retriever(Protocol):
    def invoke(self, query: str) -> list[Document]:
        ...


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, docs: list[Document]):
        self.vector_store = vector_store
        self.bm25 = BM25Retriever.from_documents(docs, k=5)
        self.vector_retriever = vector_store.store.as_retriever(search_kwargs={"k": 5})
        self.weights = [0.3, 0.7]

    def retrieve(self, query: str, k: int = 5) -> list[Document]:
        bm25_docs = self.bm25.invoke(query)
        vector_docs = self.vector_retriever.invoke(query)
        return _weighted_merge([bm25_docs, vector_docs], self.weights)[:k]


def _weighted_merge(
    results: list[list[Document]], weights: list[float]
) -> list[Document]:
    scored: dict[str, tuple[float, Document]] = {}
    for weight, docs in zip(weights, results):
        for rank, doc in enumerate(docs):
            doc_id = doc.metadata.get("source", str(id(doc)))
            score, existing = scored.get(doc_id, (0.0, doc))
            scored[doc_id] = (score + weight / (rank + 1), existing)
    ranked = sorted(scored.values(), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked]


def query_expansion(query: str, llm) -> list[str]:
    prompt = (
        f"Generate 3 alternative phrasings of the following query for search retrieval. "
        f"Return each on a new line, no numbering.\nQuery: {query}"
    )
    response = llm.invoke(prompt)
    alternatives = [line.strip() for line in response.content.split("\n") if line.strip()]
    return [query] + alternatives[:3]


def rrf_fusion(results: list[list[Document]], k: int = 60) -> list[Document]:
    scores: dict[str, tuple[float, Document]] = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_id = doc.metadata.get("source", str(id(doc)))
            if doc_id not in scores:
                scores[doc_id] = (0.0, doc)
            score, _ = scores[doc_id]
            scores[doc_id] = (score + 1.0 / (k + rank + 1), doc)

    ranked = sorted(scores.values(), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked]
