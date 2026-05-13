from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import SessionInfo
from app.services.session_service import SessionService

router = APIRouter()
session_service = SessionService()


@router.get("/sessions/{room_name}", response_model=SessionInfo)
async def get_session(room_name: str):
    """Get session information for a room."""
    session = await session_service.get_session(room_name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(
        room_name=session.get("room_name", room_name),
        identity=session.get("identity", ""),
        status=session.get("status", "unknown"),
        started_at=session.get("started_at"),
        ended_at=session.get("ended_at"),
        message_count=int(session.get("message_count", 0)),
        metadata={},
    )


@router.delete("/sessions/{room_name}")
async def end_session(room_name: str):
    """End a session."""
    await session_service.end_session(room_name)
    return {"message": "Session ended", "room_name": room_name}