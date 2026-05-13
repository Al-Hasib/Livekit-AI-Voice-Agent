from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Enums ────────────────────────────────────────────────────────────────────


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    ERROR = "error"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Token ────────────────────────────────────────────────────────────────────


class TokenRequest(BaseModel):
    identity: str = Field(..., min_length=1, max_length=128, description="Participant identity")
    room_name: str = Field(..., min_length=1, max_length=128, description="Room name")
    metadata: str | None = Field(default=None, max_length=1024)


class TokenResponse(BaseModel):
    token: str
    room_name: str
    identity: str
    server_url: str


# ── Documents ────────────────────────────────────────────────────────────────


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: DocumentStatus
    chunks: int
    message: str


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    status: DocumentStatus
    chunks: int
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


class DocumentDeleteResponse(BaseModel):
    doc_id: str
    deleted: bool
    message: str


# ── Sessions ─────────────────────────────────────────────────────────────────


class SessionInfo(BaseModel):
    room_name: str
    identity: str
    status: SessionStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    message_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Health ───────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    services: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── RAG Query ────────────────────────────────────────────────────────────────


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2048)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
    latency_ms: float


# ── Validators ───────────────────────────────────────────────────────────────


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    doc_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_markdown: bool = False

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        settings_max_mb = 50  # fallback
        max_chars = settings_max_mb * 1024 * 1024
        if len(v) > max_chars:
            raise ValueError(f"Text exceeds maximum size of {settings_max_mb}MB")
        return v