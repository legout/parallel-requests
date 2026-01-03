from fastreq.exceptions import (
    BackendError,
    ConfigurationError,
    FailureDetails,
    FastRequestsError,
    PartialFailureError,
    ProxyError,
    RateLimitExceededError,
    RetryExhaustedError,
    ValidationError,
)
from fastreq.config import GlobalConfig
from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig
from fastreq.client import (
    FastRequests,
    RequestOptions,
    ReturnType,
    fastreq,
    fastreq_async,
)

__version__ = "2.0.0"

__all__ = [
    "__version__",
    "FastRequestsError",
    "BackendError",
    "ProxyError",
    "RetryExhaustedError",
    "RateLimitExceededError",
    "ValidationError",
    "ConfigurationError",
    "PartialFailureError",
    "FailureDetails",
    "GlobalConfig",
    "Backend",
    "RequestConfig",
    "NormalizedResponse",
    "FastRequests",
    "RequestOptions",
    "ReturnType",
    "fastreq",
    "fastreq_async",
    "ParallelRequestsError",
    "ParallelRequests",
]


__doc__ = """fastreq - High-performance parallel HTTP client

A Python library for executing parallel HTTP requests with built-in retry logic,
proxy rotation, rate limiting, and support for multiple HTTP backends (niquests,
aiohttp, and requests).

Basic usage:

    >>> from fastreq import fastreq
    >>> results = fastreq(
    ...     urls=["https://api.github.com/repos/python/cpython"],
    ...     concurrency=3,
    ... )
    >>> print(results[0]['name'])
    'cpython'

Async usage:

    >>> import asyncio
    >>> from fastreq import fastreq_async
    >>> async def main():
    ...     results = await fastreq_async(
    ...         urls=["https://httpbin.org/get"],
    ...     )
    ...     return results
    >>> asyncio.run(main())

Features:
    - Automatic backend detection (niquests → aiohttp → requests)
    - HTTP/2 support (niquests backend)
    - Exponential backoff with jitter
    - Token bucket rate limiting
    - Proxy rotation with validation
    - User-agent rotation
    - Session cookie management
    - Flexible response parsing (JSON, text, content, response, stream)
    - Custom parse functions
    - Keyed response mapping
    - Graceful failure handling

Backends:
    - niquests: HTTP/2 support, streaming, async native (recommended)
    - aiohttp: Streaming support, async native
    - requests: Sync-first, streaming via thread wrapper
"""

ParallelRequestsError = FastRequestsError
ParallelRequests = FastRequests
