from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.config import get_settings
from app.utils.exceptions import SessionError

logger = structlog.get_logger(__name__)


class SessionService:
    """Manages voice agent sessions via Redis."""

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    def _session_key(self, room_name: str) -> str:
        return f"session:{room_name}"

    async def create_session(
        self,
        room_name: str,
        identity: str,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        try:
            redis = await self._get_redis()
            settings = get_settings()
            key = self._session_key(room_name)

            session_data = {
                "room_name": room_name,
                "identity": identity,
                "status": "active",
                "started_at": datetime.utcnow().isoformat(),
                "message_count": 0,
                "metadata": json.dumps(metadata or {}),
            }

            await redis.hset(key, mapping=session_data)
            await redis.expire(key, settings.session_ttl)

            logger.info("session_created", room=room_name, identity=identity)
            return session_data
        except Exception as e:
            raise SessionError(f"Failed to create session: {e}") from e

    async def get_session(self, room_name: str) -> dict[str, Any] | None:
        try:
            redis = await self._get_redis()
            key = self._session_key(room_name)
            data = await redis.hgetall(key)
            return data if data else None
        except Exception as e:
            logger.error("get_session_failed", room=room_name, error=str(e))
            return None

    async def end_session(self, room_name: str) -> None:
        try:
            redis = await self._get_redis()
            key = self._session_key(room_name)
            await redis.hset(key, "status", "ended")
            await redis.hset(key, "ended_at", datetime.utcnow().isoformat())
        except Exception as e:
            logger.error("end_session_failed", room=room_name, error=str(e))

    async def increment_message_count(self, room_name: str) -> None:
        try:
            redis = await self._get_redis()
            key = self._session_key(room_name)
            await redis.hincrby(key, "message_count", 1)
        except Exception as e:
            logger.error("increment_message_failed", room=room_name, error=str(e))

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None