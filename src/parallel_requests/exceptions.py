from dataclasses import dataclass
from typing import Any


@dataclass
class FailureDetails:
    url: str
    error: Exception
    attempt: int = 0


class ParallelRequestsError(Exception):
    """Base exception for parallel-requests library."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)


class BackendError(ParallelRequestsError):
    """Raised when a backend operation fails."""

    def __init__(
        self, message: str, backend_name: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.backend_name = backend_name
        super().__init__(message, *args, **kwargs)


class ProxyError(ParallelRequestsError):
    """Raised when a proxy operation fails."""

    def __init__(
        self, message: str, proxy_url: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.proxy_url = proxy_url
        super().__init__(message, *args, **kwargs)


class RetryExhaustedError(ParallelRequestsError):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int = 0,
        last_error: Exception | None = None,
        url: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.attempts = attempts
        self.last_error = last_error
        self.url = url
        super().__init__(message, *args, **kwargs)


class RateLimitExceededError(ParallelRequestsError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, *args, **kwargs)


class ValidationError(ParallelRequestsError):
    """Raised when request validation fails."""

    def __init__(
        self, message: str, field_name: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.field_name = field_name
        super().__init__(message, *args, **kwargs)


class ConfigurationError(ParallelRequestsError):
    """Raised when configuration is invalid."""

    def __init__(
        self, message: str, config_key: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.config_key = config_key
        super().__init__(message, *args, **kwargs)


class PartialFailureError(ParallelRequestsError):
    """Raised when some requests succeed and others fail."""

    def __init__(
        self,
        message: str,
        failures: dict[str, FailureDetails] | None = None,
        successes: int = 0,
        total: int = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.failures = failures or {}
        self.successes = successes
        self.total = total
        super().__init__(message, *args, **kwargs)

    def get_failed_urls(self) -> list[str]:
        """Return list of URLs that failed."""
        return list(self.failures.keys())
