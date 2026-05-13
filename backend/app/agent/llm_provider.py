from __future__ import annotations

import structlog
from livekit.plugins import openai

from app.config import get_settings
from app.utils.exceptions import LLMError

logger = structlog.get_logger(__name__)


def create_llm() -> openai.LLM:
    """Create and configure the LLM provider.

    Uses OpenAI GPT-4o-mini for optimal speed/quality tradeoff.
    Streaming is enabled by default in LiveKit's OpenAI plugin.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise LLMError("OPENAI_API_KEY is required")

    llm = openai.LLM(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
        api_key=settings.openai_api_key,
    )

    logger.info(
        "llm_configured",
        provider=settings.llm_provider,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
    )

    return llm