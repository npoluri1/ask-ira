"""Response caching layer for MCP server results.

Supports Redis (production) and in-memory (development) backends.
Reduces redundant MCP calls for identical/similar queries.
"""

import hashlib
import json
import time
from typing import Any, Optional

from src.config import get_settings

settings = get_settings()


class CacheBackend:
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: int) -> None:
        raise NotImplementedError

    async def clear(self) -> None:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expires = self._store[key]
            if time.time() < expires:
                return value
            del self._store[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = (value, time.time() + (ttl or self._default_ttl))

    async def clear(self) -> None:
        self._store.clear()


class ResponseCache:
    def __init__(self, backend: Optional[CacheBackend] = None):
        self._backend = backend or MemoryCache()

    def _make_key(self, prefix: str, data: dict) -> str:
        raw = f"{prefix}:{json.dumps(data, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get_mcp_result(self, server: str, query: str) -> Optional[str]:
        key = self._make_key(f"mcp:{server}", {"query": query})
        return await self._backend.get(key)

    async def set_mcp_result(self, server: str, query: str, result: str, ttl: int = 300) -> None:
        key = self._make_key(f"mcp:{server}", {"query": query})
        await self._backend.set(key, result, ttl)

    async def clear(self) -> None:
        await self._backend.clear()


_cache: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    global _cache
    if _cache is None:
        _cache = ResponseCache()
    return _cache
