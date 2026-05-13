from __future__ import annotations


class VoiceAgentError(Exception):
    """Base exception for voice agent."""
    pass


class STTError(VoiceAgentError):
    """Speech-to-text failure."""
    pass


class TTSError(VoiceAgentError):
    """Text-to-speech failure."""
    pass


class LLMError(VoiceAgentError):
    """LLM failure."""
    pass


class RAGError(VoiceAgentError):
    """RAG retrieval or ingestion failure."""
    pass


class DocumentError(VoiceAgentError):
    """Document processing error."""
    pass


class TokenError(VoiceAgentError):
    """Token generation error."""
    pass


class RateLimitError(VoiceAgentError):
    """Rate limit exceeded."""
    pass


class SessionError(VoiceAgentError):
    """Session management error."""
    pass