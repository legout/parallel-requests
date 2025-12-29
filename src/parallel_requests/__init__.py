from parallel_requests.exceptions import (
    ConfigurationError,
    FailureDetails,
    ParallelRequestsError,
    PartialFailureError,
    ProxyError,
    RateLimitExceededError,
    RetryExhaustedError,
    ValidationError,
    BackendError,
)
from parallel_requests.config import GlobalConfig
from parallel_requests.backends.base import Backend, NormalizedResponse, RequestConfig
from parallel_requests.client import (
    ParallelRequests,
    RequestOptions,
    ReturnType,
    parallel_requests,
    parallel_requests_async,
)

__version__ = "2.0.0"

__all__ = [
    "__version__",
    "ParallelRequestsError",
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
    "ParallelRequests",
    "RequestOptions",
    "ReturnType",
    "parallel_requests",
    "parallel_requests_async",
]


__doc__ = """Parallel Requests - High-performance parallel HTTP client

A Python library for executing parallel HTTP requests with built-in retry logic,
proxy rotation, rate limiting, and support for multiple HTTP backends (niquests,
aiohttp, and requests).

Basic usage:

    >>> from parallel_requests import parallel_requests
    >>> results = parallel_requests(
    ...     urls=["https://api.github.com/repos/python/cpython"],
    ...     concurrency=3,
    ... )
    >>> print(results[0]['name'])
    'cpython'

Async usage:

    >>> import asyncio
    >>> from parallel_requests import parallel_requests_async
    >>> async def main():
    ...     results = await parallel_requests_async(
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
