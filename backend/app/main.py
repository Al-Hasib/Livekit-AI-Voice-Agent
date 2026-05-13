#!/usr/bin/env python3
"""FastAPI server for the Voice Agent backend.

Handles:
- LiveKit token generation
- Document upload and RAG management
- Session management
- Health checks
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import get_settings
from app.utils.logger import setup_logger
from app.api import api_router
from app.services.session_service import SessionService
from app.utils.exceptions import VoiceAgentError

logger = structlog.get_logger(__name__)

# Global session service for cleanup
_session_service: SessionService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    setup_logger(settings.log_level)

    global _session_service
    _session_service = SessionService()

    logger.info("app_starting", environment=settings.environment)

    yield

    # Cleanup
    if _session_service:
        await _session_service.close()

    logger.info("app_stopping")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Voice Agent API",
        version="1.0.0",
        description="AI Voice Agent with LiveKit and RAG",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(api_router)

    # Global exception handler
    @app.exception_handler(VoiceAgentError)
    async def voice_agent_error_handler(request: Request, exc: VoiceAgentError):
        logger.error("voice_agent_error", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "type": type(exc).__name__},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )