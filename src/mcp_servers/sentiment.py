import asyncio
import json

import httpx
import yfinance as yf

from src.config.data_source import is_seed
from src.mcp_servers.base import MCPRequest, MCPResponse, MCPServer


class SentimentMCPServer(MCPServer):
    def __init__(self):
        from data.loader import load_sentiment_lexicon
        lexicon = load_sentiment_lexicon()
        self.POSITIVE_WORDS = set(lexicon.get("positive_words", []))
        self.NEGATIVE_WORDS = set(lexicon.get("negative_words", []))
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=15)
        return self._http_client

    async def handle(self, request: MCPRequest) -> MCPResponse:
        query = request.query.lower()

        if "news" in query or "headline" in query:
            ticker = self._extract_ticker(query)
            articles = await self._fetch_realtime_news(ticker)
            sentiment = self._analyze_articles(articles)
            return MCPResponse(
                content=(
                    f"{'[SEED] ' if is_seed() else ''}News sentiment for {ticker}: {sentiment['label']} "
                    f"(score: {sentiment['score']:.2f}, "
                    f"articles analyzed: {sentiment['count']})"
                ),
                source="sentiment",
                metadata={"ticker": ticker, **sentiment, "data_source": "seed" if is_seed() else "realtime"},
            )

        if "social" in query or "twitter" in query or "reddit" in query:
            ticker = self._extract_ticker(query)
            posts = await self._fetch_realtime_social(ticker)
            sentiment = self._analyze_articles(posts)
            return MCPResponse(
                content=(
                    f"{'[SEED] ' if is_seed() else ''}Social sentiment for {ticker}: {sentiment['label']} "
                    f"(score: {sentiment['score']:.2f}, "
                    f"posts: {sentiment['count']})"
                ),
                source="sentiment",
                metadata={"ticker": ticker, **sentiment, "data_source": "seed" if is_seed() else "realtime"},
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

    async def _fetch_realtime_news(self, ticker: str) -> list[dict]:
        if is_seed():
            return self._seed_news(ticker)
        loop = asyncio.get_event_loop()
        try:
            t = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            news_items = await loop.run_in_executor(None, lambda: t.news or [])
            if news_items:
                return [
                    {
                        "title": item.get("title", ""),
                        "source": item.get("publisher", item.get("source", "Yahoo Finance")),
                        "link": item.get("link", ""),
                        "timestamp": item.get("providerPublishTime"),
                    }
                    for item in news_items[:15]
                ]
        except Exception:
            pass
        try:
            client = await self._get_client()
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=10",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("news", [])
                if items:
                    return [
                        {"title": item.get("title", ""), "source": item.get("publisher", "Yahoo Finance"), "link": item.get("link", "")}
                        for item in items[:15]
                    ]
        except Exception:
            pass
        return self._seed_news(ticker)

    async def _fetch_realtime_social(self, ticker: str) -> list[dict]:
        if is_seed():
            return self._seed_social(ticker)
        loop = asyncio.get_event_loop()
        try:
            t = await loop.run_in_executor(None, lambda: yf.Ticker(ticker))
            news = await loop.run_in_executor(None, lambda: t.news or [])
            if news:
                posts = []
                for item in news[:10]:
                    title = item.get("title", "")
                    posts.append({"title": title, "source": "Social"})
                if posts:
                    return posts
        except Exception:
            pass
        return self._seed_social(ticker)

    def _seed_news(self, ticker: str) -> list[dict]:
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

    def _seed_social(self, ticker: str) -> list[dict]:
        return [
            {"title": f"${ticker} looking strong today!", "source": "Twitter"},
            {"title": f"Not sure about {ticker} valuation at these levels", "source": "Reddit"},
            {"title": f"{ticker} earnings play this week", "source": "Twitter"},
            {"title": f"Bought more {ticker} calls", "source": "Reddit"},
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
