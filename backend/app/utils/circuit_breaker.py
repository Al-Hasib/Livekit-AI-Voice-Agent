from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for external service calls.

    States:
        CLOSED  → Normal operation, calls pass through
        OPEN    → Failures exceeded threshold, calls are rejected
        HALF_OPEN → Testing recovery, limited calls pass through
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("circuit_half_open", breaker=self.name)
        return self._state

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        async with self._lock:
            state = self.state

            if state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is open. Retry after {self.recovery_timeout}s"
                )

            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is half-open with pending test call"
                    )
                self._half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("circuit_closed", breaker=self.name)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("circuit_reopened", breaker=self.name)
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_opened",
                    breaker=self.name,
                    failures=self._failure_count,
                    threshold=self.failure_threshold,
                )


class CircuitOpenError(Exception):
    pass