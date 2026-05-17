from pathlib import Path

from src.config import get_settings
from src.rag.embeddings import get_embedding_model

settings = get_settings()


class VectorStore:
    def __init__(self, provider: str = "local"):
        self.embeddings = get_embedding_model(provider)
        persist = Path(settings.chroma_persist_dir)
        persist.mkdir(parents=True, exist_ok=True)
        try:
            from langchain_chroma import Chroma
            self.store = Chroma(
                collection_name="ask_ira_docs",
                embedding_function=self.embeddings,
                persist_directory=str(persist),
            )
        except ImportError:
            from langchain_community.vectorstores import Chroma as Chroma
            self.store = Chroma(
                collection_name="ask_ira_docs",
                embedding_function=self.embeddings,
                persist_directory=str(persist),
            )

    def add_documents(self, documents):
        self.store.add_documents(documents)

    def similarity_search(self, query: str, k: int = 5):
        return self.store.similarity_search(query, k=k)

    def max_marginal_relevance_search(self, query: str, k: int = 5, fetch_k: int = 20):
        return self.store.max_marginal_relevance_search(query, k=k, fetch_k=fetch_k)

    def count(self) -> int:
        """Returns the number of documents in the collection."""
        try:
            # For langchain-chroma
            if hasattr(self.store, "_collection"):
                return self.store._collection.count()
            # Fallback
            res = self.store.get()
            return len(res["ids"]) if res and "ids" in res else 0
        except Exception:
            return 0
