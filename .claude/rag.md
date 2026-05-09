# RAG Pipeline Standards

Rules for the hybrid retrieval-augmented generation pipeline in `src/rag/`.

## Pipeline Architecture

```
Query → Query Expansion (3 LLM variants)
      → BM25 Sparse Retrieval
      → Dense Embedding Similarity
      → RRF Fusion (k=60)
      → Cross-Encoder Reranking
      → Top-k Documents
```

## Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| `VectorStore` | `vector_store.py` | ChromaDB wrapper (add, similarity_search, MMR) |
| `HybridRetriever` | `retrieval.py` | BM25 + dense ensemble |
| `query_expansion` | `retrieval.py` | LLM generates 3 alternative phrasings |
| `rrf_fusion` | `retrieval.py` | Reciprocal Rank Fusion with k=60 |
| `CrossEncoderReranker` | `reranking.py` | Cross-encoder re-scoring of candidates |
| `RAGPipeline` | `pipeline.py` | Orchestrator: wires all stages together |

## Embedding Config

```python
# src/rag/embeddings.py
# Model: sentence-transformers/all-MiniLM-L6-v2
# Dimensions: 384
# Distance: cosine similarity

# Configurable via Settings:
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
EMBEDDING_TOP_K = 5
```

## Chunking Rules

1. Documents stored as full text in `page_content`
2. Metadata fields: `source` (str), `ticker` (str, optional), `sector` (str, optional), `topic` (str, optional)
3. No chunking — each document is stored as a single entry

## Evaluation Targets

```bash
python -m scripts.run_eval
```

| Metric | Target | Description |
|--------|--------|-------------|
| `context_recall` | >0.83 | Retrieved docs cover ground truth |
| `faithfulness` | >0.91 | Answer is grounded in retrieved docs |
| `answer_relevancy` | >0.84 | Answer is relevant to the question |
| `context_precision` | >0.80 | Retrieved docs are all relevant |

## Seeding Rules

1. Seed data in `data/company_descriptions.json` (7 documents: 4 companies + 3 frameworks)
2. Run seeder: `ask-ira-seed` or `python -m scripts.seed_data`
3. Persist directory: `CHROMA_PERSIST_DIR` from settings (default: `./data/chroma`)
4. ChromaDB data is gitignored (`.gitignore` excludes `data/chroma_db/`)

## Adding New Documents

```python
from src.rag.vector_store import VectorStore
from langchain_core.documents import Document

doc = Document(
    page_content="Company: new data here",
    metadata={"source": "my_source", "ticker": "ABC"},
)
store = VectorStore()
store.add_documents([doc])
```
