from __future__ import annotations

from fastapi import APIRouter

from .health import router as health_router
from .token import router as token_router
from .documents import router as documents_router
from .sessions import router as sessions_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router, tags=["health"])
api_router.include_router(token_router, tags=["tokens"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(sessions_router, tags=["sessions"])