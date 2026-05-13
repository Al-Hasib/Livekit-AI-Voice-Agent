from __future__ import annotations

import structlog
from livekit.plugins import cartesia

from app.config import get_settings
from app.utils.exceptions import TTSError

logger = structlog.get_logger(__name__)


def create_tts() -> cartesia.TTS:
    """Create and configure the TTS (Text-to-Speech) provider.

    Uses Cartesia Sonic for lowest latency (~100ms first byte).
    """
    settings = get_settings()

    if not settings.cartesia_api_key:
        raise TTSError("CARTESIA_API_KEY is required")

    tts = cartesia.TTS(
        model=settings.cartesia_model,
        voice_id=settings.cartesia_voice_id,
        speed=settings.cartesia_speed,
        api_key=settings.cartesia_api_key,
        language="en",
    )

    logger.info(
        "tts_configured",
        provider=settings.tts_provider,
        model=settings.cartesia_model,
        voice_id=settings.cartesia_voice_id,
    )

    return tts