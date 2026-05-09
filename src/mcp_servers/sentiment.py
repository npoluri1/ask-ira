from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class SentimentMCPServer(MCPServer):
    def __init__(self):
        from data.loader import load_sentiment_lexicon
        lexicon = load_sentiment_lexicon()
        self.POSITIVE_WORDS = set(lexicon.get("positive_words", []))
        self.NEGATIVE_WORDS = set(lexicon.get("negative_words", []))

    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "news" in query or "headline" in query:
            ticker = self._extract_ticker(query)
            articles = await self._fetch_news(ticker)
            sentiment = self._analyze_articles(articles)
            return MCPResponse(
                content=(
                    f"News sentiment for {ticker}: {sentiment['label']} "
                    f"(score: {sentiment['score']:.2f}, "
                    f"articles analyzed: {sentiment['count']})"
                ),
                source="sentiment",
                metadata={"ticker": ticker, **sentiment},
            )

        if "social" in query or "twitter" in query or "reddit" in query:
            ticker = self._extract_ticker(query)
            posts = await self._fetch_social_posts(ticker)
            sentiment = self._analyze_social(posts)
            return MCPResponse(
                content=(
                    f"Social sentiment for {ticker}: {sentiment['label']} "
                    f"(score: {sentiment['score']:.2f}, "
                    f"posts: {sentiment['count']})"
                ),
                source="sentiment",
                metadata={"ticker": ticker, **sentiment},
            )

        return MCPResponse(
            content=(
                "Sentiment analysis available for news headlines "
                "and social media posts. Specify a ticker."
            ),
            source="sentiment",
        )

    def _extract_ticker(self, query: str) -> str:
        words = query.upper().split()
        for w in words:
            if w.isalpha() and len(w) <= 5:
                return w
        return "AAPL"

    async def _fetch_news(self, ticker: str) -> list[dict]:
        from data.loader import load_news_articles
        articles = load_news_articles(ticker)
        if articles:
            return [{"title": a["title"], "source": a["source"]} for a in articles[:10]]
        return [
            {"title": f"{ticker} beats earnings estimates, shares rally", "source": "Reuters"},
            {"title": f"Analysts upgrade {ticker} citing strong growth", "source": "Bloomberg"},
            {"title": f"{ticker} faces regulatory headwinds in EU", "source": "FT"},
            {"title": f"New product launch boosts {ticker} outlook", "source": "CNBC"},
            {"title": f"{ticker} supply chain concerns persist", "source": "WSJ"},
        ]

    def _analyze_articles(self, articles: list[dict]) -> dict:
        scores = []
        for a in articles:
            title_lower = a["title"].lower()
            pos = sum(1 for w in self.POSITIVE_WORDS if w in title_lower)
            neg = sum(1 for w in self.NEGATIVE_WORDS if w in title_lower)
            scores.append((pos - neg) / max(pos + neg, 1))
        avg = sum(scores) / max(len(scores), 1)
        return {
            "score": avg,
            "label": "bullish" if avg > 0.2 else "bearish" if avg < -0.2 else "neutral",
            "count": len(articles),
        }

    def _analyze_social(self, posts: list[dict]) -> dict:
        return self._analyze_articles(posts)

    async def _fetch_social_posts(self, ticker: str) -> list[dict]:
        return [
            {"title": f"${ticker} looking strong today!", "source": "Twitter"},
            {"title": f"Not sure about {ticker} valuation at these levels", "source": "Reddit"},
            {"title": f"{ticker} earnings play this week", "source": "Twitter"},
            {"title": f"Bought more {ticker} calls", "source": "Reddit"},
        ]
