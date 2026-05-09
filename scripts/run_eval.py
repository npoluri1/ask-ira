"""Run RAGAS evaluation on the Ask IRA RAG pipeline."""

import asyncio

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from src.rag.pipeline import RAGPipeline
from src.rag.vector_store import VectorStore
from src.utils.llm import get_llm

TEST_QUERIES = [
    {
        "question": "What is Apple's main business and key products?",
        "expected": "Apple designs iPhones, Macs, iPads, and provides services like App Store and Apple Music.",
    },
    {
        "question": "What is the recommended portfolio allocation strategy?",
        "expected": "Core-satellite approach with 70% core holdings and 30% satellite positions.",
    },
]


async def main():
    llm = get_llm()
    store = VectorStore()
    docs = store.similarity_search("sample query", k=10)
    pipeline = RAGPipeline(store, docs)

    data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    for item in TEST_QUERIES:
        retrieved = pipeline.retrieve(item["question"], llm=llm)
        answer = retrieved[0].page_content if retrieved else "No answer found"

        data["question"].append(item["question"])
        data["answer"].append(answer)
        data["contexts"].append([d.page_content for d in retrieved])
        data["ground_truth"].append(item["expected"])

    dataset = Dataset.from_dict(data)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    )

    print("RAGAS Evaluation Results:")
    for metric, score in result.items():
        print(f"  {metric}: {score:.4f}")
    print("\nTarget: recall >0.83, faithfulness >0.91, relevance >0.84")


if __name__ == "__main__":
    asyncio.run(main())
