import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from loguru import logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_second: Maximum requests per second
        burst: Maximum burst size (tokens)
        max_concurrency: Maximum concurrent requests
    """

    requests_per_second: float
    burst: int
    max_concurrency: int = 20


class TokenBucket:
    """Token bucket algorithm for rate limiting.

    Implements the token bucket algorithm to control request rate with
    burst capability.

    Example:
        >>> bucket = TokenBucket(requests_per_second=10, burst=5)
        >>> await bucket.acquire()  # Wait if needed
        >>> bucket.available()
        4

    Args:
        requests_per_second: Token refill rate
        burst: Maximum bucket size (tokens)
    """

    def __init__(self, requests_per_second: float, burst: int) -> None:
        self.requests_per_second = requests_per_second
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now
        self._tokens = min(self.burst, self._tokens + elapsed * self.requests_per_second)

    def available(self) -> int:
        """Get available tokens.

        Returns:
            Number of tokens currently available
        """
        self._refill_tokens()
        return int(self._tokens)

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire
        """
        while True:
            self._refill_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            wait_time = (tokens - self._tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)


class AsyncRateLimiter:
    """Async rate limiter using token bucket algorithm.

    Combines token bucket rate limiting with a semaphore for concurrency control.

    Example:
        >>> from parallel_requests.utils.rate_limiter import AsyncRateLimiter, RateLimitConfig
        >>> config = RateLimitConfig(requests_per_second=10, burst=5, max_concurrency=20)
        >>> limiter = AsyncRateLimiter(config)
        >>> async with limiter.acquire():
        ...     # Make request here
        ...     pass

    Args:
        config: Rate limiting configuration
    """

    def __init__(self, config: RateLimitConfig) -> None:
        self.config = config
        self._bucket = TokenBucket(config.requests_per_second, config.burst)
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Acquire rate limit token and concurrency slot.

        Yields:
            None when both token and slot are acquired
        """
        async with self._semaphore:
            logger.debug(f"Rate limiter acquiring token (available: {self._bucket.available()})")
            await self._bucket.acquire()
            yield

    def available(self) -> int:
        """Get available tokens.

        Returns:
            Number of tokens currently available
        """
        return self._bucket.available()
