from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import BinaryIO

import aiofiles
import structlog

from app.config import get_settings
from app.agent.rag.service import RAGService
from app.agent.rag import DocumentChunker, QdrantVectorStore, EmbeddingService
from app.utils.exceptions import DocumentError

logger = structlog.get_logger(__name__)


class DocumentService:
    """Handles document upload, processing, and deletion."""

    def __init__(self, rag_service: RAGService | None = None):
        settings = get_settings()
        self.rag_service = rag_service or RAGService()
        self.upload_dir = os.path.join(os.getcwd(), "uploads")
        self.max_size = settings.max_upload_size_mb * 1024 * 1024
        self.allowed_ext = set(settings.allowed_extensions)

    def _validate_file(self, filename: str, size: int) -> None:
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in self.allowed_ext:
            raise DocumentError(
                f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(self.allowed_ext))}"
            )

        if size > self.max_size:
            raise DocumentError(
                f"File size {size} exceeds maximum {self.max_size} bytes"
            )

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        size: int,
        metadata: dict | None = None,
    ) -> dict:
        """Upload and process a file for RAG."""
        self._validate_file(filename, size)
        doc_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["filename"] = filename
        metadata["uploaded_at"] = datetime.utcnow().isoformat()

        # Save file to disk
        os.makedirs(self.upload_dir, exist_ok=True)
        file_path = os.path.join(self.upload_dir, f"{doc_id}_{filename}")

        try:
            async with aiofiles.open(file_path, "wb") as f:
                content = file.read()
                await f.write(content)
        except Exception as e:
            raise DocumentError(f"Failed to save file: {e}") from e

        # Read and process text
        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            text = content.decode("latin-1", errors="replace")

        is_markdown = filename.lower().endswith(".md")

        try:
            result_doc_id = await self.rag_service.ingest_text(
                text=text,
                doc_id=doc_id,
                metadata=metadata,
                is_markdown=is_markdown,
            )

            logger.info("document_processed", doc_id=result_doc_id, filename=filename)
            return {
                "doc_id": result_doc_id,
                "filename": filename,
                "status": "completed",
                "chunks": 0,  # Will be populated
                "message": "Document processed successfully",
            }
        except Exception as e:
            logger.error("document_processing_failed", doc_id=doc_id, error=str(e))
            # Clean up file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise DocumentError(f"Failed to process document: {e}") from e

    async def upload_text(
        self,
        text: str,
        filename: str = "inline.txt",
        doc_id: str | None = None,
        metadata: dict | None = None,
        is_markdown: bool = False,
    ) -> dict:
        """Process inline text for RAG."""
        metadata = metadata or {}
        metadata["filename"] = filename
        metadata["uploaded_at"] = datetime.utcnow().isoformat()

        try:
            result_doc_id = await self.rag_service.ingest_text(
                text=text,
                doc_id=doc_id,
                metadata=metadata,
                is_markdown=is_markdown,
            )

            return {
                "doc_id": result_doc_id,
                "filename": filename,
                "status": "completed",
                "chunks": 0,
                "message": "Text processed successfully",
            }
        except Exception as e:
            raise DocumentError(f"Failed to process text: {e}") from e

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        result = await self.rag_service.delete_document(doc_id)

        # Also clean up file
        for f in os.listdir(self.upload_dir):
            if f.startswith(f"{doc_id}_"):
                os.remove(os.path.join(self.upload_dir, f))

        return result