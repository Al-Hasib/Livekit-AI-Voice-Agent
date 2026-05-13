from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import structlog

from app.config import get_settings
from .cache import RAGCache
from .chunker import Chunk, DocumentChunker
from .embeddings import EmbeddingService
from .vectorstore import QdrantVectorStore
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.exceptions import RAGError

logger = structlog.get_logger(__name__)


class RAGService:
    """High-level RAG service that orchestrates retrieval, caching, and ingestion.

    Optimized for lowest latency:
    - Local embeddings (FastEmbed) — no network
    - Redis query cache — avoid vector search for repeated queries
    - Circuit breaker for Qdrant — fail gracefully
    - Async throughout — no blocking calls
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        cache: RAGCache | None = None,
        chunker: DocumentChunker | None = None,
    ):
        settings = get_settings()
        self.vector_store = vector_store or QdrantVectorStore()
        self.cache = cache or RAGCache()
        self.chunker = chunker or DocumentChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )
        self.embedding = self.vector_store.embedding

        # Circuit breaker for Qdrant
        self._qdrant_cb = CircuitBreaker(
            name="qdrant",
            failure_threshold=settings.cb_failure_threshold,
            recovery_timeout=settings.cb_recovery_timeout,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
        filter_doc_ids: list[str] | None = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Returns list of dicts with: content, doc_id, score, metadata
        """
        settings = get_settings()
        top_k = top_k or settings.rag_top_k
        score_threshold = score_threshold or settings.rag_score_threshold

        if not settings.rag_enabled:
            logger.debug("rag_disabled")
            return []

        start = time.monotonic()

        # Check cache first
        if use_cache:
            try:
                cached = await self.cache.get(query, top_k)
                if cached is not None:
                    logger.debug(
                        "rag_cache_hit",
                        query=query[:50],
                        latency_ms=round((time.monotonic() - start) * 1000, 2),
                    )
                    return cached
            except Exception as e:
                logger.warning("cache_lookup_failed", error=str(e))

        # Vector search with circuit breaker
        try:
            results = await self._qdrant_cb.call(
                self.vector_store.search,
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                filter_doc_ids=filter_doc_ids,
            )
        except Exception as e:
            logger.error("rag_retrieval_failed", query=query[:50], error=str(e))
            # Graceful degradation: return empty, let LLM use general knowledge
            return []

        latency_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(
            "rag_retrieval",
            query=query[:50],
            results=len(results),
            latency_ms=latency_ms,
        )

        # Cache results
        if use_cache and results:
            asyncio.create_task(self.cache.set(query, top_k, results))

        return results

    async def ingest_text(
        self,
        text: str,
        doc_id: str | None = None,
        metadata: dict | None = None,
        is_markdown: bool = False,
    ) -> str:
        """Ingest a text document into the vector store."""
        doc_id = doc_id or str(uuid.uuid4())
        metadata = metadata or {}
        metadata["source_type"] = metadata.get("source_type", "text")

        # Chunk
        if is_markdown:
            chunks = self.chunker.chunk_markdown(text, doc_id, metadata)
        else:
            chunks = self.chunker.chunk_text(text, doc_id, metadata)

        if not chunks:
            raise RAGError("No chunks produced from document")

        # Upsert
        try:
            count = await self._qdrant_cb.call(
                self.vector_store.upsert_chunks,
                chunks=chunks,
            )
        except Exception as e:
            raise RAGError(f"Failed to upsert chunks: {e}") from e

        # Invalidate cache
        asyncio.create_task(self.cache.invalidate())

        logger.info("document_ingested", doc_id=doc_id, chunks=count)
        return doc_id

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its chunks."""
        try:
            result = await self._qdrant_cb.call(
                self.vector_store.delete_by_doc_id,
                doc_id=doc_id,
            )
            asyncio.create_task(self.cache.invalidate(doc_id))
            return result
        except Exception as e:
            logger.error("document_delete_failed", doc_id=doc_id, error=str(e))
            return False

    async def get_context_string(
        self,
        query: str,
        top_k: int | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Retrieve context and format as a string for LLM injection.

        This is the main method called by the voice pipeline.
        """
        settings = get_settings()
        max_tokens = max_tokens or settings.rag_max_context_tokens

        results = await self.retrieve(query, top_k=top_k)

        if not results:
            return ""

        # Build context string with source attribution
        context_parts = []
        current_tokens = 0

        for i, result in enumerate(results, 1):
            content = result["content"]
            score = result.get("score", 0)
            doc_id = result.get("doc_id", "unknown")

            # Rough token estimation (1 token ≈ 4 chars)
            estimated_tokens = len(content) // 4
            if current_tokens + estimated_tokens > max_tokens:
                # Truncate this chunk
                remaining = max_tokens - current_tokens
                content = content[: remaining * 4] + "..."
                context_parts.append(f"[Source {i} (score: {score:.2f}, doc: {doc_id})]:\n{content}")
                break

            context_parts.append(f"[Source {i} (score: {score:.2f}, doc: {doc_id})]:\n{content}")
            current_tokens += estimated_tokens

        return "\n\n---\n\n".join(context_parts)

    async def health_check(self) -> dict[str, Any]:
        """Check health of RAG components."""
        health: dict[str, Any] = {"rag_enabled": get_settings().rag_enabled}

        try:
            count = await self.vector_store.count_documents()
            health["vector_store"] = "healthy"
            health["document_count"] = count
        except Exception as e:
            health["vector_store"] = f"unhealthy: {e}"

        try:
            query_vec = await self.embedding.embed_query("health check")
            health["embedding_service"] = "healthy"
            health["embedding_dim"] = len(query_vec)
        except Exception as e:
            health["embedding_service"] = f"unhealthy: {e}"

        return health