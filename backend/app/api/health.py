from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.agent.rag import RAGService
from app.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    settings = get_settings()
    services = {}

    # Check RAG
    try:
        rag = RAGService()
        rag_health = await rag.health_check()
        services["rag"] = rag_health
    except Exception as e:
        services["rag"] = {"status": "unhealthy", "error": str(e)}

    # Check Redis
    try:
        from app.services.session_service import SessionService
        session_svc = SessionService()
        redis = await session_svc._get_redis()
        await redis.ping()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"unhealthy: {e}"

    overall = "healthy"
    for svc_name, svc_data in services.items():
        if isinstance(svc_data, str) and "unhealthy" in svc_data:
            overall = "degraded"
            break
        if isinstance(svc_data, dict) and svc_data.get("vector_store", "").startswith("unhealthy"):
            overall = "degraded"
            break

    return HealthResponse(
        status=overall,
        version="1.0.0",
        environment=settings.environment,
        services=services,
        timestamp=datetime.utcnow(),
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check — can the service accept traffic?"""
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """Liveness check — is the process alive?"""
    return {"alive": True}