from __future__ import annotations

import structlog
from livekit.plugins import silero

from app.config import get_settings

logger = structlog.get_logger(__name__)


def create_vad() -> silero.VAD:
    """Create and configure the VAD (Voice Activity Detection) provider.

    Uses Silero VAD which runs locally for minimal latency (~10ms).
    """
    settings = get_settings()

    vad = silero.VAD.load(
        min_speech_duration=settings.vad_min_speech_duration,
        prefix_padding_ms=int(settings.vad_prefix_padding * 1000),
        silence_threshold=settings.vad_silence_threshold,
    )

    logger.info(
        "vad_configured",
        provider=settings.vad_provider,
        min_speech_duration=settings.vad_min_speech_duration,
        silence_threshold=settings.vad_silence_threshold,
    )

    return vad