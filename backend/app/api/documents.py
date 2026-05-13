from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, Form

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentDeleteResponse,
    IngestTextRequest,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.document_service import DocumentService
from app.agent.rag import RAGService
from app.utils.exceptions import DocumentError, RAGError

router = APIRouter()
doc_service = DocumentService()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
):
    """Upload a file for RAG ingestion."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        content = await file.read()
        result = await doc_service.upload_file(
            file=file.file,
            filename=file.filename,
            size=len(content),
        )
        return DocumentUploadResponse(**result)
    except DocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.post("/documents/text", response_model=DocumentUploadResponse)
async def ingest_text(request: IngestTextRequest):
    """Ingest text directly for RAG."""
    try:
        result = await doc_service.upload_text(
            text=request.text,
            doc_id=request.doc_id,
            metadata=request.metadata,
            is_markdown=request.is_markdown,
        )
        return DocumentUploadResponse(**result)
    except DocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(doc_id: str):
    """Delete a document and its chunks."""
    try:
        deleted = await doc_service.delete_document(doc_id)
        return DocumentDeleteResponse(
            doc_id=doc_id,
            deleted=deleted,
            message="Document deleted" if deleted else "Document not found",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")


@router.post("/documents/query", response_model=RAGQueryResponse)
async def query_documents(request: RAGQueryRequest):
    """Query the RAG system directly (for testing/debugging)."""
    try:
        import time
        start = time.monotonic()
        rag = RAGService()
        results = await rag.retrieve(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            use_cache=True,
        )
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return RAGQueryResponse(
            query=request.query,
            results=results,
            latency_ms=latency_ms,
        )
    except RAGError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")