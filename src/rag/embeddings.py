from src.config import get_settings

settings = get_settings()


def get_embedding_model(provider: str = "local"):
    if provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.openai_api_key,
            )
        except ImportError:
            pass

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except ImportError:
        pass

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings as HFEmb
        return HFEmb(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except ImportError:
        pass

    from langchain_core.embeddings import Embeddings

    class _DummyEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return [[0.0] * settings.embedding_dimensions for _ in texts]
        def embed_query(self, text):
            return [0.0] * settings.embedding_dimensions

    return _DummyEmbeddings()
