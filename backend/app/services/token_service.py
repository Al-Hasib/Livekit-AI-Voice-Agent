from __future__ import annotations

from datetime import timedelta

import structlog
from livekit.api import AccessToken, VideoGrants

from app.config import get_settings
from app.utils.exceptions import TokenError

logger = structlog.get_logger(__name__)


class TokenService:
    """Generates LiveKit access tokens for client connections."""

    def __init__(self):
        self._settings = get_settings()

    def create_token(
        self,
        identity: str,
        room_name: str,
        metadata: str | None = None,
        ttl: timedelta | None = None,
    ) -> str:
        try:
            ttl = ttl or timedelta(hours=6)

            token = AccessToken(
                self._settings.livekit_api_key,
                self._settings.livekit_api_secret,
            )
            token.identity = identity
            token.ttl = ttl

            if metadata:
                token.metadata = metadata

            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
            token.add_grant(grants)

            jwt_token = token.to_jwt()
            logger.info("token_created", identity=identity, room=room_name)
            return jwt_token

        except Exception as e:
            logger.error("token_creation_failed", error=str(e))
            raise TokenError(f"Failed to create token: {e}") from e