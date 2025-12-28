import asyncio
import random
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from ..exceptions import RetryExhaustedError


@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff_multiplier: float = 1.0
    jitter: float = 0.1
    retry_on: set[type[Exception]] | None = None
    dont_retry_on: set[type[Exception]] | None = None


class RetryStrategy:
    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()

    def _calculate_delay(self, attempt: int) -> float:
        base_delay = self.config.backoff_multiplier * (2**attempt)
        jitter_amount = self.config.jitter * base_delay
        jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)
        return float(max(0, jittered_delay))

    def _should_retry(self, error: Exception) -> bool:
        if self.config.dont_retry_on and isinstance(error, tuple(self.config.dont_retry_on)):
            return False
        if self.config.retry_on:
            return isinstance(error, tuple(self.config.retry_on))
        return True

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e

                if not self._should_retry(e):
                    raise

                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)

        raise RetryExhaustedError(
            message=f"Retry attempts exhausted after {self.config.max_retries} retries",
            attempts=self.config.max_retries,
            last_error=last_error,
        )
