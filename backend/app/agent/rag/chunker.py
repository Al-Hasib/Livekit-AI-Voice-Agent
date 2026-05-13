from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)


@dataclass
class Chunk:
    content: str
    metadata: dict
    chunk_index: int
    doc_id: str


class DocumentChunker:
    """Splits documents into semantically meaningful chunks."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def chunk_text(
        self,
        text: str,
        doc_id: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        metadata = metadata or {}

        # Pre-process: normalize whitespace
        text = self._normalize_text(text)
        if not text.strip():
            return []

        # Split using recursive character splitter
        splits = self._splitter.split_text(text)

        chunks = []
        for idx, split in enumerate(splits):
            if not split.strip():
                continue
            chunk = Chunk(
                content=split.strip(),
                metadata={**metadata, "chunk_index": idx},
                chunk_index=idx,
                doc_id=doc_id,
            )
            chunks.append(chunk)

        return chunks

    def chunk_markdown(
        self,
        text: str,
        doc_id: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        """Chunk markdown with header-aware splitting."""
        metadata = metadata or {}
        text = self._normalize_text(text)

        try:
            md_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "h1"),
                    ("##", "h2"),
                    ("###", "h3"),
                ]
            )
            md_splits = md_splitter.split_text(text)
        except Exception:
            return self.chunk_text(text, doc_id, metadata)

        chunks = []
        for idx, md_split in enumerate(md_splits):
            sub_text = md_split.page_content
            sub_meta = {**metadata, **md_split.metadata}

            if len(sub_text) <= self.chunk_size:
                chunks.append(
                    Chunk(
                        content=sub_text.strip(),
                        metadata={**sub_meta, "chunk_index": idx},
                        chunk_index=idx,
                        doc_id=doc_id,
                    )
                )
            else:
                sub_chunks = self._splitter.split_text(sub_text)
                for sub_idx, sc in enumerate(sub_chunks):
                    chunks.append(
                        Chunk(
                            content=sc.strip(),
                            metadata={**sub_meta, "chunk_index": idx + sub_idx},
                            chunk_index=idx + sub_idx,
                            doc_id=doc_id,
                        )
                    )

        return chunks

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()