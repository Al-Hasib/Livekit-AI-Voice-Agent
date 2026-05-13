from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import get_settings
from .chunker import Chunk
from .embeddings import EmbeddingService

logger = structlog.get_logger(__name__)


class QdrantVectorStore:
    """Qdrant vector store for RAG document retrieval."""

    def __init__(
        self,
        collection_name: str | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        settings = get_settings()
        self.collection_name = collection_name or settings.qdrant_collection
        self.embedding = embedding_service or EmbeddingService()

        self._client: QdrantClient | None = None
        self._initialized = False
        self._lock = asyncio.Lock()

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            settings = get_settings()
            kwargs: dict[str, Any] = {"url": settings.qdrant_url}
            if settings.qdrant_api_key:
                kwargs["api_key"] = settings.qdrant_api_key
            self._client = QdrantClient(**kwargs)
        return self._client

    async def ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        async with self._lock:
            if self._initialized:
                return

            client = self._get_client()
            settings = get_settings()

            collections = client.get_collections().collections
            names = [c.name for c in collections]

            if self.collection_name not in names:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.embedding_dim,
                        distance=Distance.COSINE,
                        on_disk=False,
                    ),
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=20000,
                    ),
                    hnsw_config=models.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000,
                    ),
                )
                logger.info("created_collection", collection=self.collection_name)

            self._initialized = True

    async def upsert_chunks(self, chunks: list[Chunk]) -> int:
        """Insert document chunks into the vector store."""
        await self.ensure_collection()
        client = self._get_client()

        if not chunks:
            return 0

        texts = [c.content for c in chunks]
        embeddings = await self.embedding.embed_documents(texts)

        points = []
        for chunk, vector in zip(chunks, embeddings):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk.doc_id}:{chunk.chunk_index}"))
            payload = {
                "content": chunk.content,
                "doc_id": chunk.doc_id,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata,
            }
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            client.upsert(
                collection_name=self.collection_name,
                points=batch,
                wait=False,
            )

        logger.info("upserted_chunks", count=len(points), doc_id=chunks[0].doc_id if chunks else None)
        return len(points)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filter_doc_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar documents."""
        await self.ensure_collection()
        client = self._get_client()

        query_vector = await self.embedding.embed_query(query)

        search_filter = None
        if filter_doc_ids:
            search_filter = Filter(
                should=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                    for doc_id in filter_doc_ids
                ]
            )

        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=search_filter,
        )

        return [
            {
                "content": hit.payload["content"],
                "doc_id": hit.payload.get("doc_id", ""),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "score": hit.score,
                "metadata": {
                    k: v for k, v in hit.payload.items()
                    if k not in ("content", "doc_id", "chunk_index")
                },
            }
            for hit in results
        ]

    async def delete_by_doc_id(self, doc_id: str) -> bool:
        """Delete all chunks for a document."""
        client = self._get_client()

        try:
            client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                    ]
                ),
            )
            logger.info("deleted_doc_chunks", doc_id=doc_id)
            return True
        except Exception as e:
            logger.error("delete_chunks_failed", doc_id=doc_id, error=str(e))
            return False

    async def count_documents(self) -> int:
        """Count unique documents in the collection."""
        client = self._get_client()
        try:
            info = client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0