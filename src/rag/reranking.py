from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[Document], top_k: int = 3) -> list[Document]:
        pairs = [[query, doc.page_content] for doc in documents]
        scores = self.model.predict(pairs)
        scored = list(zip(scores, documents))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
