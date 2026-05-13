from __future__ import annotations

import time
from typing import Any

import structlog
from livekit.agents import llm, AutoSubscribe, JobContext
from livekit.agents.voice import VoicePipelineAgent

from app.config import get_settings
from app.agent.rag.service import RAGService
from app.agent.stt_provider import create_stt
from app.agent.tts_provider import create_tts
from app.agent.llm_provider import create_llm
from app.agent.vad_provider import create_vad
from app.utils.exceptions import VoiceAgentError

logger = structlog.get_logger(__name__)

# Global RAG service (shared across sessions)
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


# ── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful, knowledgeable voice assistant. Follow these rules:

1. Be concise and conversational — this is a voice interaction, not a text chat.
2. Use the provided context to answer questions accurately.
3. If the context doesn't contain relevant information, say you don't have specific information about that, then offer your general knowledge.
4. Never make up information that isn't in the context or your training data.
5. Keep responses under 2-3 sentences unless the user asks for detail.
6. If you're unsure, ask for clarification rather than guessing.
7. Be friendly but professional.
"""


def create_chat_context() -> llm.ChatContext:
    """Create initial chat context with system prompt."""
    return llm.ChatContext().append(role="system", text=SYSTEM_PROMPT)


# ── Callbacks ────────────────────────────────────────────────────────────────


async def before_llm_callback(
    agent: VoicePipelineAgent,
    chat_ctx: llm.ChatContext,
) -> llm.ChatContext | None:
    """Called before each LLM invocation to inject RAG context.

    This is the key integration point: retrieve relevant documents
    and inject them as context into the chat context.
    """
    settings = get_settings()

    if not settings.rag_enabled:
        return None

    # Extract last user message for retrieval
    last_user_msg = ""
    for msg in reversed(chat_ctx.messages):
        if msg.role == "user":
            if isinstance(msg.content, str):
                last_user_msg = msg.content
            elif isinstance(msg.content, list):
                # Content might be a list of parts
                last_user_msg = " ".join(
                    part.text if hasattr(part, "text") else str(part)
                    for part in msg.content
                )
            break

    if not last_user_msg or len(last_user_msg.strip()) < 3:
        logger.debug("no_user_message_for_rag")
        return None

    start = time.monotonic()

    try:
        rag_service = get_rag_service()
        context_string = await rag_service.get_context_string(last_user_msg)

        latency_ms = round((time.monotonic() - start) * 1000, 2)

        if not context_string:
            logger.debug("rag_no_context", latency_ms=latency_ms)
            return None

        # Inject RAG context as a system message
        rag_message = (
            "The following context was retrieved from the knowledge base. "
            "Use it to answer the user's question if relevant:\n\n"
            f"{context_string}"
        )

        logger.info(
            "rag_context_injected",
            query=last_user_msg[:50],
            latency_ms=latency_ms,
            context_length=len(context_string),
        )

        # Append RAG context to chat context
        chat_ctx = chat_ctx.append(role="system", text=rag_message)
        return chat_ctx

    except Exception as e:
        logger.error(
            "rag_injection_failed",
            error=str(e),
            latency_ms=round((time.monotonic() - start) * 1000, 2),
        )
        # Graceful degradation: proceed without RAG context
        return None


async def on_user_turn_completed(
    agent: VoicePipelineAgent,
    chat_ctx: llm.ChatContext,
) -> None:
    """Called when user finishes speaking."""
    settings = get_settings()

    # Edge case: limit conversation length
    if len(chat_ctx.messages) > settings.max_conversation_turns * 2:
        logger.warning("max_conversation_turns_reached", turns=settings.max_conversation_turns)
        # Could truncate old messages here
        pass


async def on_agent_started(agent: VoicePipelineAgent) -> None:
    """Called when the agent starts for a new session."""
    logger.info("agent_session_started")


async def on_agent_stopped(agent: VoicePipelineAgent) -> None:
    """Called when the agent stops."""
    logger.info("agent_session_stopped")


# ── Pipeline Factory ─────────────────────────────────────────────────────────


def create_voice_pipeline() -> VoicePipelineAgent:
    """Create the VoicePipelineAgent with all providers configured.

    Latency budget:
    - VAD (Silero, local):        ~10ms
    - STT (Deepgram streaming):   ~200ms
    - RAG (FastEmbed + Qdrant):   ~20-50ms
    - LLM (OpenAI streaming):     ~300-500ms first token
    - TTS (Cartesia streaming):   ~100ms first byte
    ──────────────────────────────────────────
    Total:                        ~630-860ms
    """
    settings = get_settings()

    # Create providers
    vad = create_vad()
    stt = create_stt()
    tts = create_tts()
    llm_provider = create_llm()

    # Create initial chat context
    chat_ctx = create_chat_context()

    # Build pipeline
    agent = VoicePipelineAgent(
        vad=vad,
        stt=stt,
        llm=llm_provider,
        tts=tts,
        chat_ctx=chat_ctx,
        # Low-latency optimizations
        allow_interruptions=settings.allow_interruptions,
        interrupt_min_words=settings.interrupt_min_words,
        min_endpointing_delay=settings.min_endpointing_delay,
        # RAG callback
        before_llm_cb=before_llm_callback,
    )

    logger.info("voice_pipeline_created")
    return agent