from __future__ import annotations

import structlog
from livekit.plugins import deepgram

from app.config import get_settings
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.exceptions import STTError

logger = structlog.get_logger(__name__)


def create_stt() -> deepgram.STT:
    """Create and configure the STT (Speech-to-Text) provider.

    Uses Deepgram Nova-3 for lowest latency (~200ms streaming).
    """
    settings = get_settings()

    if not settings.deepgram_api_key:
        raise STTError("DEEPGRAM_API_KEY is required")

    stt = deepgram.STT(
        model=settings.deepgram_model,
        language=settings.deepgram_language,
        smart_format=settings.deepgram_smart_format,
        api_key=settings.deepgram_api_key,
        # Streaming for lowest latency
        interim_results=True,
        punctuate=True,
        profanity_filter=False,
    )

    logger.info(
        "stt_configured",
        provider=settings.stt_provider,
        model=settings.deepgram_model,
        language=settings.deepgram_language,
    )

    return stt