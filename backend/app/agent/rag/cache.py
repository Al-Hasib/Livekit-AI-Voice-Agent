from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class RAGCache:
    """Redis-based cache for RAG retrieval results.

    Caches query → document results to avoid repeated vector searches
    for identical or similar queries.
    """

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
        return self._redis

    @staticmethod
    def _cache_key(query: str, top_k: int) -> str:
        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16]
        return f"rag:cache:{query_hash}:{top_k}"

    async def get(self, query: str, top_k: int = 5) -> list[dict[str, Any]] | None:
        try:
            redis = await self._get_redis()
            key = self._cache_key(query, top_k)
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("cache_get_failed", error=str(e))
        return None

    async def set(
        self,
        query: str,
        top_k: int,
        results: list[dict[str, Any]],
        ttl: int | None = None,
    ) -> None:
        try:
            settings = get_settings()
            redis = await self._get_redis()
            key = self._cache_key(query, top_k)
            ttl = ttl or settings.rag_cache_ttl
            await redis.setex(key, ttl, json.dumps(results, default=str))
        except Exception as e:
            logger.warning("cache_set_failed", error=str(e))

    async def invalidate(self, doc_id: str | None = None) -> None:
        """Invalidate cache entries. If doc_id is given, only invalidate related."""
        try:
            redis = await self._get_redis()
            if doc_id is None:
                # Clear all RAG cache
                async for key in redis.scan_iter("rag:cache:*"):
                    await redis.delete(key)
            else:
                # Best-effort: clear all since we can't easily filter by doc_id in key
                async for key in redis.scan_iter("rag:cache:*"):
                    cached = await redis.get(key)
                    if cached and doc_id in cached:
                        await redis.delete(key)
        except Exception as e:
            logger.warning("cache_invalidation_failed", error=str(e))

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None