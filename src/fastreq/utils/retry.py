import asyncio
import random
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from ..exceptions import RetryExhaustedError
from loguru import logger


@dataclass
class RetryConfig:
    """Configuration for retry strategy.

    Attributes:
        max_retries: Maximum number of retry attempts
        backoff_multiplier: Base multiplier for exponential backoff (seconds)
        jitter: Jitter amount as fraction of backoff (0.1 = 10%)
        retry_on: Exception types to retry (None = retry all)
        dont_retry_on: Exception types to never retry
    """

    max_retries: int = 3
    backoff_multiplier: float = 1.0
    jitter: float = 0.1
    retry_on: set[type[Exception]] | None = None
    dont_retry_on: set[type[Exception]] | None = None


class RetryStrategy:
    """Retry strategy with exponential backoff and jitter.

    Implements exponential backoff with configurable jitter for
    resilient request handling.

    Example:
        >>> from fastreq.utils.retry import RetryStrategy, RetryConfig
        >>> config = RetryConfig(max_retries=3, backoff_multiplier=1.0, jitter=0.1)
        >>> strategy = RetryStrategy(config)
        >>> result = await strategy.execute(some_async_function)

    Args:
        config: Retry configuration (uses defaults if None)
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt.

        Uses exponential backoff with jitter:
        delay = backoff_multiplier * (2^attempt) ± (jitter * delay)

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        base_delay = self.config.backoff_multiplier * (2**attempt)
        jitter_amount = self.config.jitter * base_delay
        jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)
        return float(max(0, jittered_delay))

    def _should_retry(self, error: Exception) -> bool:
        """Determine if error should trigger a retry.

        Args:
            error: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
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
        """Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retry attempts exhausted
            Exception: If error is not retryable
        """
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
                    logger.debug(
                        f"Retry attempt {attempt + 1}/{self.config.max_retries}: {e}, waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)

        logger.error(f"All retries exhausted after {self.config.max_retries} attempts")
        raise RetryExhaustedError(
            message=f"Retry attempts exhausted after {self.config.max_retries} retries",
            attempts=self.config.max_retries,
            last_error=last_error,
        )
