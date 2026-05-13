from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


def default_retry(
    max_attempts: int = 3,
    base_wait: float = 1.0,
    max_wait: float = 10.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator factory for default retry logic with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        return retry(
            retry=retry_if_exception_type(retry_exceptions),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_wait, max=max_wait),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )(func)

    return decorator


async def retry_async(
    func: Callable[..., T],
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
    max_attempts: int = 3,
    base_wait: float = 1.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Async retry utility with exponential backoff."""
    kwargs = kwargs or {}

    for attempt in range(1, max_attempts + 1):
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except retry_exceptions as e:
            if attempt == max_attempts:
                raise
            wait = base_wait * (2 ** (attempt - 1))
            logger.warning(
                "retry_attempt",
                func=func.__name__,
                attempt=attempt,
                max_attempts=max_attempts,
                wait=wait,
                error=str(e),
            )
            await asyncio.sleep(wait)

    raise RuntimeError("Unreachable")


import logging