#!/usr/bin/env python3
"""CLI tool to ingest documents into the RAG knowledge base.

Usage:
    python ingest-docs.py --file document.txt
    python ingest-docs.py --dir ./docs/
    python ingest-docs.py --text "Some text to ingest"
    python ingest-docs.py --file doc.md --markdown
"""

import argparse
import asyncio
import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.agent.rag import RAGService
from app.utils.logger import setup_logger


async def ingest_file(file_path: str, is_markdown: bool = False) -> None:
    """Ingest a single file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    if not text.strip():
        print(f"⚠️  Skipping empty file: {file_path}")
        return

    filename = os.path.basename(file_path)
    rag = RAGService()

    start = time.monotonic()
    doc_id = await rag.ingest_text(
        text=text,
        metadata={
            "filename": filename,
            "file_path": file_path,
            "source_type": "file",
        },
        is_markdown=is_markdown,
    )
    elapsed = round((time.monotonic() - start) * 1000, 2)

    print(f"✅ Ingested: {filename} → doc_id={doc_id} ({elapsed}ms)")


async def ingest_directory(dir_path: str, is_markdown: bool = False) -> None:
    """Ingest all files in a directory."""
    valid_extensions = {".txt", ".md", ".json", ".csv"}
    files = []

    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in valid_extensions:
                files.append(os.path.join(root, filename))

    if not files:
        print(f"⚠️  No supported files found in: {dir_path}")
        return

    print(f"📄 Found {len(files)} files to ingest")

    for file_path in files:
        md = is_markdown or file_path.endswith(".md")
        await ingest_file(file_path, is_markdown=md)

    print(f"\n🎉 Ingested {len(files)} files")


async def ingest_text(text: str, is_markdown: bool = False) -> None:
    """Ingest inline text."""
    rag = RAGService()

    start = time.monotonic()
    doc_id = await rag.ingest_text(
        text=text,
        metadata={"source_type": "cli"},
        is_markdown=is_markdown,
    )
    elapsed = round((time.monotonic() - start) * 1000, 2)

    print(f"✅ Ingested text → doc_id={doc_id} ({elapsed}ms)")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into RAG knowledge base")
    parser.add_argument("--file", "-f", help="Path to file to ingest")
    parser.add_argument("--dir", "-d", help="Path to directory of files to ingest")
    parser.add_argument("--text", "-t", help="Inline text to ingest")
    parser.add_argument("--markdown", "-m", action="store_true", help="Parse as markdown")

    args = parser.parse_args()

    setup_logger("INFO")

    if args.file:
        asyncio.run(ingest_file(args.file, args.markdown))
    elif args.dir:
        asyncio.run(ingest_directory(args.dir, args.markdown))
    elif args.text:
        asyncio.run(ingest_text(args.text, args.markdown))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()