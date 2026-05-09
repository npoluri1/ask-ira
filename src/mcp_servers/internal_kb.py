from data.loader import load_knowledge_base
from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class InternalKBMCPServer(MCPServer):
    def __init__(self):
        raw = load_knowledge_base()
        self._articles = [
            {
                "id": a["id"],
                "title": a["title"],
                "content": a["content"],
            }
            for a in raw
        ]

    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()
        matches = []

        for article in self._articles:
            score = self._match_score(query, article)
            if score > 0:
                matches.append((score, article))

        matches.sort(key=lambda x: x[0], reverse=True)

        if not matches:
            return MCPResponse(
                content="No matching internal knowledge found.",
                source="internal_kb",
            )

        top = matches[0][1]
        return MCPResponse(
            content=f"[{top['id']}] {top['title']}: {top['content']}",
            source="internal_kb",
            metadata={"matched_articles": len(matches), "top_match": top["id"]},
        )

    def _match_score(self, query: str, article: dict) -> float:
        query_terms = set(query.split())
        title_terms = set(article["title"].lower().split())
        content_terms = set(article["content"].lower().split())

        title_matches = len(query_terms & title_terms)
        content_matches = len(query_terms & content_terms)

        return title_matches * 3 + content_matches
