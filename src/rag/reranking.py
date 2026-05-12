from langchain_core.documents import Document


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self._model_name)
            except ImportError:
                self._model = None
        return self._model

    def rerank(self, query: str, documents: list[Document], top_k: int = 3) -> list[Document]:
        model = self._get_model()
        if model is None:
            return documents[:top_k]
        pairs = [[query, doc.page_content] for doc in documents]
        scores = model.predict(pairs)
        scored = list(zip(scores, documents))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
