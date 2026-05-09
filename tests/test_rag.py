import pytest
from langchain_core.documents import Document

from src.rag.retrieval import rrf_fusion
from src.rag.vector_store import VectorStore


@pytest.fixture
def sample_docs():
    return [
        Document(page_content="Apple makes iPhones", metadata={"source": "doc1"}),
        Document(page_content="Apple provides cloud services", metadata={"source": "doc2"}),
        Document(page_content="Microsoft makes Windows", metadata={"source": "doc3"}),
    ]


def test_rrf_fusion(sample_docs):
    result = rrf_fusion([sample_docs[:2], sample_docs[1:]])
    assert len(result) == 3
    assert result[0].page_content == "Apple provides cloud services"


def test_rrf_fusion_empty():
    result = rrf_fusion([[], []])
    assert result == []


def test_rrf_fusion_single_list(sample_docs):
    result = rrf_fusion([sample_docs])
    assert len(result) == 3


def test_vector_store_initialization():
    store = VectorStore()
    assert store.store is not None
    assert store.embeddings is not None


@pytest.mark.asyncio
async def test_vector_store_add_and_search():
    store = VectorStore()
    docs = [
        Document(page_content="Investment analysis for Apple Inc.", metadata={"ticker": "AAPL"}),
        Document(page_content="Microsoft cloud revenue growth", metadata={"ticker": "MSFT"}),
    ]
    store.add_documents(docs)
    results = store.similarity_search("Apple investment", k=2)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_vector_store_mmr():
    store = VectorStore()
    docs = [
        Document(page_content="Apple iPhone sales growth", metadata={"ticker": "AAPL"}),
        Document(page_content="Apple services division", metadata={"ticker": "AAPL"}),
        Document(page_content="Microsoft Azure cloud", metadata={"ticker": "MSFT"}),
    ]
    store.add_documents(docs)
    results = store.max_marginal_relevance_search("Apple", k=3)
    assert len(results) > 0
