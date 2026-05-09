from langchain_core.documents import Document

from src.rag.reranking import CrossEncoderReranker
from src.rag.retrieval import HybridRetriever, query_expansion, rrf_fusion
from src.rag.vector_store import VectorStore


class RAGPipeline:
    def __init__(self, vector_store: VectorStore, docs: list[Document] | None = None):
        self.vector_store = vector_store
        self.hybrid = HybridRetriever(vector_store, docs or [])
        self.reranker = CrossEncoderReranker()
        self.query_expander = None

    def retrieve(self, query: str, llm=None, k: int = 5) -> list[Document]:
        if llm:
            self.query_expander = query_expansion
            queries = query_expansion(query, llm)
            all_results = [self.hybrid.retrieve(q, k=k) for q in queries]
            fused = rrf_fusion(all_results)
        else:
            fused = self.hybrid.retrieve(query, k=k)

        return self.reranker.rerank(query, fused, top_k=k)
