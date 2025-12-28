import asyncio
import time
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    requests_per_second: float
    burst: int
    max_concurrency: int = 20


class TokenBucket:
    def __init__(self, requests_per_second: float, burst: int) -> None:
        self.requests_per_second = requests_per_second
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()

    def _refill_tokens(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now
        self._tokens = min(self.burst, self._tokens + elapsed * self.requests_per_second)

    def available(self) -> int:
        self._refill_tokens()
        return int(self._tokens)

    async def acquire(self, tokens: int = 1) -> None:
        while True:
            self._refill_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            wait_time = (tokens - self._tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)


class AsyncRateLimiter:
    def __init__(self, config: RateLimitConfig) -> None:
        self.config = config
        self._bucket = TokenBucket(config.requests_per_second, config.burst)
        self._semaphore = asyncio.Semaphore(config.max_concurrency)

    async def acquire(self) -> None:
        async with self._semaphore:
            await self._bucket.acquire()

    def available(self) -> int:
        return self._bucket.available()
