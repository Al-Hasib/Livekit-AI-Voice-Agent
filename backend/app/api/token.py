from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import TokenRequest, TokenResponse
from app.services.token_service import TokenService
from app.utils.exceptions import TokenError

router = APIRouter()
token_service = TokenService()


@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest):
    """Generate a LiveKit access token for a participant."""
    try:
        settings = get_settings()
        jwt_token = token_service.create_token(
            identity=request.identity,
            room_name=request.room_name,
            metadata=request.metadata,
        )
        return TokenResponse(
            token=jwt_token,
            room_name=request.room_name,
            identity=request.identity,
            server_url=settings.livekit_url,
        )
    except TokenError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {e}")