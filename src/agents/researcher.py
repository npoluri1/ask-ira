from langchain_core.messages import HumanMessage, SystemMessage

from src.cache import get_cache
from src.mcp_servers.registry import MCPRegistry
from src.rag.pipeline import RAGPipeline
from src.rag.vector_store import VectorStore
from src.utils.llm import get_llm

SYSTEM_PROMPT = """You are the Researcher Agent for Ask IRA.
Gather data by dispatching queries to MCP servers and RAG.
Summarize findings from each source concisely."""


class ResearcherAgent:
    def __init__(self, registry: MCPRegistry):
        self.llm = get_llm(temperature=0.0)
        self.registry = registry
        self.cache = get_cache()
        self._rag: RAGPipeline | None = None

    def _get_rag(self) -> RAGPipeline:
        if self._rag is None:
            try:
                vs = VectorStore()
                self._rag = RAGPipeline(vs)
            except Exception:
                self._rag = RAGPipeline.__new__(RAGPipeline)
        return self._rag

    async def research(self, query: str) -> dict:
        try:
            raw_results = await self.registry.dispatch_all(query)
        except Exception:
            raw_results = {}

        summaries = {}
        for name, response in raw_results.items():
            summaries[name] = response.content

        rag_context = []
        try:
            rag = self._get_rag()
            rag_docs = rag.retrieve(query, k=3)
            rag_context = [doc.page_content for doc in rag_docs]
        except Exception:
            pass

        context_parts = [f"[{k}]: {v}" for k, v in summaries.items()]
        if rag_context:
            context_parts.append(f"RAG context:\n{chr(10).join(rag_context)}")

        synthesis_msg = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Query: {query}\n\nResearch results:\n"
                    + "\n".join(context_parts)
                    + "\n\nProvide a concise synthesis of findings."
                )
            ),
        ])

        return {
            "mcp_results": summaries,
            "rag_context": rag_context,
            "synthesis": synthesis_msg.content,
            "next": "analyst",
        }
