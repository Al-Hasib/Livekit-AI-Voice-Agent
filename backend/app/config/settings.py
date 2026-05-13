from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────
    app_name: str = "voice-agent"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # ── LiveKit ───────────────────────────────────────────
    livekit_url: str = "ws://livekit:7880"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # ── STT ───────────────────────────────────────────────
    stt_provider: Literal["deepgram"] = "deepgram"
    deepgram_api_key: str = ""
    deepgram_language: str = "en-US"
    deepgram_model: str = "nova-3"
    deepgram_smart_format: bool = True

    # ── LLM ───────────────────────────────────────────────
    llm_provider: Literal["openai"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 512
    llm_timeout: float = 15.0

    # ── TTS ───────────────────────────────────────────────
    tts_provider: Literal["cartesia"] = "cartesia"
    cartesia_api_key: str = ""
    cartesia_model: str = "sonic-english"
    cartesia_voice_id: str = "694f9389-aac1-45b6-b726-9d9369183238"
    cartesia_speed: float = 1.0

    # ── VAD ───────────────────────────────────────────────
    vad_provider: Literal["silero"] = "silero"
    vad_silence_threshold: float = 0.6
    vad_prefix_padding: float = 0.5
    vad_min_speech_duration: float = 0.25

    # ── RAG ───────────────────────────────────────────────
    rag_enabled: bool = True
    rag_top_k: int = 5
    rag_score_threshold: float = 0.5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64
    rag_max_context_tokens: int = 3000

    # ── Vector Store ──────────────────────────────────────
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "voice_agent_docs"
    qdrant_api_key: str = ""

    # ── Embeddings ────────────────────────────────────────
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # ── Redis ─────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"
    rag_cache_ttl: int = 3600
    session_ttl: int = 86400

    # ── Agent Behaviour ───────────────────────────────────
    min_endpointing_delay: float = 0.5
    allow_interruptions: bool = True
    interrupt_min_words: int = 3
    max_conversation_turns: int = 200
    max_turn_duration: float = 120.0

    # ── Circuit Breaker ───────────────────────────────────
    cb_failure_threshold: int = 5
    cb_recovery_timeout: float = 30.0
    cb_half_open_max: int = 1

    # ── Rate Limit ────────────────────────────────────────
    rate_limit_per_minute: int = 60

    # ── Server ────────────────────────────────────────────
    host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    # ── Document Upload ───────────────────────────────────
    max_upload_size_mb: int = 50
    allowed_extensions: list[str] = [".txt", ".md", ".pdf", ".json", ".csv"]


@lru_cache
def get_settings() -> Settings:
    return Settings()