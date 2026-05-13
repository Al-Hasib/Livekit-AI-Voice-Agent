from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Sequence

import numpy as np
import structlog
from fastembed import TextEmbedding

from app.config import get_settings

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """Local embedding service using FastEmbed for lowest latency.

    Uses BAAI/bge-small-en-v1.5 by default (384 dims, ~5ms/embedding).
    No network calls needed — runs entirely on CPU.
    """

    def __init__(self, model_name: str | None = None, dim: int | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dim = dim or settings.embedding_dim
        self._model: TextEmbedding | None = None
        self._lock = asyncio.Lock()

    async def _ensure_model(self) -> TextEmbedding:
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    logger.info("loading_embedding_model", model=self.model_name)
                    self._model = TextEmbedding(self.model_name)
                    logger.info("embedding_model_loaded")
        return self._model

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        model = await self._ensure_model()
        embeddings = list(model.query_embed([text]))
        return embeddings[0].tolist()

    async def embed_documents(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Embed multiple documents in batches."""
        model = await self._ensure_model()
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = list(model.embed(batch))
            all_embeddings.extend([e.tolist() for e in batch_embeddings])

        return all_embeddings

    async def embed_single(self, text: str) -> list[float]:
        """Embed a single text (alias for documents)."""
        result = await self.embed_documents([text])
        return result[0]