import asyncio
import contextlib
import importlib
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TypeVar, overload

from .backends.base import Backend, NormalizedResponse, RequestConfig
from .exceptions import (
    ConfigurationError,
    FailureDetails,
    PartialFailureError,
)
from .utils.logging import configure_logging
from .utils.rate_limiter import AsyncRateLimiter, RateLimitConfig
from .utils.retry import RetryConfig, RetryStrategy
from loguru import logger


class ReturnType(str, Enum):
    """Enum for response parsing options.

    Attributes:
        JSON: Parse response as JSON (returns dict/list or None)
        TEXT: Return response as decoded string
        CONTENT: Return response as raw bytes
        RESPONSE: Return full NormalizedResponse object
        STREAM: Stream response content (requires stream_callback)
    """

    JSON = "json"
    TEXT = "text"
    CONTENT = "content"
    RESPONSE = "response"
    STREAM = "stream"


@dataclass
class RequestOptions:
    """Internal request options for backwards compatibility.

    Attributes:
        url: Request URL
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        headers: Request headers
        timeout: Per-request timeout in seconds
        proxy: Proxy URL
        return_type: How to parse the response
        stream_callback: Callback for streaming responses
    """

    url: str
    method: str = "GET"
    params: dict[str, Any] | None = None
    data: Any = None
    json: Any = None
    headers: dict[str, str] | None = None
    timeout: float | None = None
    proxy: str | None = None
    return_type: ReturnType = ReturnType.JSON
    stream_callback: Callable[[bytes], Any] | None = None


T = TypeVar("T")


class ParallelRequests:
    """Main client for parallel HTTP requests.

    Example:
        >>> from parallel_requests import ParallelRequests
        >>> client = ParallelRequests(concurrency=5)
        >>> async with client:
        ...     results = await client.request(
        ...         urls=["https://httpbin.org/get"] * 3,
        ...     )
        >>> print(len(results))
        3

    Args:
        backend: Backend to use ("auto", "niquests", "aiohttp", or "requests")
        concurrency: Maximum number of concurrent requests
        max_retries: Maximum retry attempts per request
        rate_limit: Requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2: Enable HTTP/2 (if supported by backend)
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
        timeout: Default timeout per request (seconds)
        cookies: Initial session cookies
        random_user_agent: Rotate user agents
        random_proxy: Enable proxy rotation (requires proxy config)
        debug: Enable debug logging
        verbose: Enable verbose output
        return_none_on_failure: Return None instead of raising on failure
    """

    def __init__(
        self,
        backend: str = "auto",
        concurrency: int = 20,
        max_retries: int = 3,
        rate_limit: float | None = None,
        rate_limit_burst: int = 5,
        http2: bool = True,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
        timeout: float | None = None,
        cookies: dict[str, str] | None = None,
        random_user_agent: bool = True,
        random_proxy: bool = False,
        debug: bool = False,
        verbose: bool = True,
        return_none_on_failure: bool = False,
    ) -> None:
        self.backend_name = backend
        self.concurrency = concurrency
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.random_user_agent = random_user_agent
        self.random_proxy = random_proxy
        self.debug = debug
        self.verbose = verbose
        self.return_none_on_failure = return_none_on_failure

        configure_logging(debug, verbose)

        self._backend: Backend | None = None
        self._cookies: dict[str, str] = cookies.copy() if cookies else {}
        self._rate_limiter: AsyncRateLimiter | None = None

        retry_config = RetryConfig(max_retries=max_retries)
        self._retry_strategy = RetryStrategy(retry_config)

        if rate_limit is not None:
            rate_limit_config = RateLimitConfig(
                requests_per_second=rate_limit,
                burst=rate_limit_burst,
                max_concurrency=concurrency,
            )
            self._rate_limiter = AsyncRateLimiter(rate_limit_config)

        self._http2 = http2
        self._select_backend()

    def _select_backend(self) -> None:
        if self.backend_name == "auto":
            backend_classes = [
                ("niquests", "NiquestsBackend"),
                ("aiohttp", "AiohttpBackend"),
                ("requests", "RequestsBackend"),
            ]

            unavailable: list[str] = []
            for backend_module, backend_class_name in backend_classes:
                try:
                    module = importlib.import_module(f"parallel_requests.backends.{backend_module}")
                    backend_cls = getattr(module, backend_class_name)
                    self._backend = backend_cls(http2_enabled=self._http2)
                    if unavailable:
                        logger.info(
                            f"Using backend: {backend_module} ({', '.join(unavailable)} unavailable)"
                        )
                    else:
                        logger.info(f"Using backend: {backend_module}")
                    return
                except ImportError:
                    unavailable.append(backend_module)
                    continue

            raise ConfigurationError(
                "No suitable backend found. Please install one of: niquests, aiohttp, or requests"
            )
        else:
            try:
                module = importlib.import_module(f"parallel_requests.backends.{self.backend_name}")
                backend_options: list[tuple[str, type[Backend]]] = [
                    (name, cls)
                    for name, cls in module.__dict__.items()
                    if isinstance(cls, type) and issubclass(cls, Backend) and cls is not Backend
                ]

                if not backend_options:
                    raise ConfigurationError(f"Backend '{self.backend_name}' not found")

                backend_cls = backend_options[0][1]
                self._backend = backend_cls(http2_enabled=self._http2)
                logger.info(f"Using backend: {self.backend_name}")
            except ImportError as e:
                raise ConfigurationError(
                    f"Failed to load backend '{self.backend_name}': {e}"
                ) from e

    async def __aenter__(self) -> "ParallelRequests":
        """Enter async context manager and initialize backend session.

        Returns:
            Self for use in async with statement
        """
        if self._backend:
            await self._backend.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager and close backend session."""
        if self._backend:
            await self._backend.__aexit__(*args)

    async def close(self) -> None:
        """Close backend session and cleanup resources."""
        if self._backend:
            await self._backend.close()

    def reset_cookies(self) -> None:
        """Clear all session cookies."""
        self._cookies = {}

    def set_cookies(self, cookies: dict[str, str]) -> None:
        """Add cookies to the session.

        Args:
            cookies: Dictionary of cookies to add (updates existing cookies)
        """
        self._cookies.update(cookies)

    @staticmethod
    @contextlib.asynccontextmanager
    async def _null_context() -> AsyncGenerator[None, None]:
        """A null async context manager to replace rate limiting when disabled."""
        yield

    # Single URL -> single result
    @overload
    async def request(
        self,
        urls: str,
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        keys: None = ...,
    ) -> Any: ...

    # List of URLs with keys -> dict result
    @overload
    async def request(
        self,
        urls: list[str],
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        keys: list[str] = ...,
    ) -> dict[str, Any]: ...

    # List of URLs without keys -> list result
    @overload
    async def request(
        self,
        urls: list[str],
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        keys: None = ...,
    ) -> list[Any]: ...

    # General overload for str | list[str] with optional keys -> Any
    @overload
    async def request(
        self,
        urls: str | list[str],
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        keys: list[str] | None = ...,
    ) -> Any: ...

    async def request(
        self,
        urls: str | list[str],
        *,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        proxy: str | None = None,
        return_type: ReturnType | str = ReturnType.JSON,
        follow_redirects: bool | None = None,
        verify_ssl: bool | None = None,
        parse_func: Callable[[Any], Any] | None = None,
        keys: list[str] | None = None,
    ) -> Any:
        """Make parallel HTTP requests.

        Args:
            urls: Single URL or list of URLs to request.
            method: HTTP method (GET, POST, etc.).
            params: Query parameters.
            data: Request body data.
            json: JSON body (serialized automatically).
            headers: Request headers.
            timeout: Per-request timeout in seconds.
            proxy: Proxy URL.
            return_type: How to parse the response (json, text, content, response).
            follow_redirects: Override default follow_redirects setting.
            verify_ssl: Override default verify_ssl setting.
            parse_func: Custom function to parse each response.
            keys: Keys for dict return (must match urls length).

        Returns:
            - Single URL: single result
            - List of URLs: list of results
            - List of URLs with keys: dict mapping keys to results
        """
        if not self._backend:
            raise ConfigurationError("Backend not initialized")

        # Normalize return_type to enum
        if isinstance(return_type, str):
            return_type = ReturnType(return_type)

        # Resolve per-request overrides
        effective_follow_redirects = (
            follow_redirects if follow_redirects is not None else self.follow_redirects
        )
        effective_verify_ssl = verify_ssl if verify_ssl is not None else self.verify_ssl
        effective_timeout = timeout if timeout is not None else self.timeout

        # Normalize single URL to list for uniform processing
        if isinstance(urls, str):
            single_url = True
            url_list: list[str] = [urls]
        else:
            single_url = False
            url_list = list(urls)

        # Validate keys if provided
        if keys is not None and len(keys) != len(url_list):
            raise ConfigurationError(
                f"Number of keys ({len(keys)}) must match number of URLs ({len(url_list)})"
            )

        # Build request options for each URL
        request_options = [
            RequestOptions(
                url=u,
                method=method,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=effective_timeout,
                proxy=proxy,
                return_type=return_type,
            )
            for u in url_list
        ]

        tasks = [
            self._execute_request(
                req,
                follow_redirects=effective_follow_redirects,
                verify_ssl=effective_verify_ssl,
            )
            for req in request_options
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures: dict[str, FailureDetails] = {}
        processed_results: list[Any] = []

        for idx, result in enumerate(results):
            current_url = url_list[idx]

            if isinstance(result, Exception):
                if self.return_none_on_failure:
                    processed_results.append(None)
                else:
                    failures[current_url] = FailureDetails(url=current_url, error=result)
                    processed_results.append(result)
            else:
                # Apply parse_func if provided
                if parse_func is not None:
                    result = parse_func(result)
                processed_results.append(result)

        if failures and not self.return_none_on_failure:
            raise PartialFailureError(
                f"Partial failure: {len(failures)} of {len(url_list)} requests failed",
                failures=failures,
                successes=len([r for r in results if not isinstance(r, Exception)]),
                total=len(url_list),
            )

        # Return based on input type and keys
        if single_url:
            return processed_results[0]
        elif keys is not None:
            return dict(zip(keys, processed_results, strict=True))
        else:
            return processed_results

    async def _execute_request(
        self,
        req: RequestOptions,
        *,
        follow_redirects: bool,
        verify_ssl: bool,
    ) -> Any:
        if not self._backend:
            raise ConfigurationError("Backend not initialized")

        backend = self._backend

        async def make_request() -> NormalizedResponse:
            rate_limit_ctx = (
                self._rate_limiter.acquire() if self._rate_limiter else self._null_context()
            )
            async with rate_limit_ctx:
                return await backend.request(
                    RequestConfig(
                        url=req.url,
                        method=req.method,
                        params=req.params,
                        data=req.data,
                        json=req.json,
                        headers=req.headers,
                        cookies={**self._cookies},
                        timeout=req.timeout,
                        proxy=req.proxy,
                        http2=self._http2,
                        stream=req.return_type == ReturnType.STREAM,
                        follow_redirects=follow_redirects,
                        verify_ssl=verify_ssl,
                    )
                )

        response = await self._retry_strategy.execute(make_request)
        return self._parse_response(response, req)

    def _parse_response(self, response: NormalizedResponse, req: RequestOptions) -> Any:
        logger.debug(f"Request completed: {req.url} - Status: {response.status_code}")
        match req.return_type:
            case ReturnType.JSON:
                return response.json_data if response.is_json else None
            case ReturnType.TEXT:
                return response.text
            case ReturnType.CONTENT:
                return response.content
            case ReturnType.RESPONSE:
                return response
            case ReturnType.STREAM:
                if req.stream_callback:
                    req.stream_callback(response.content)
                return None


def parallel_requests(
    urls: str | list[str],
    *,
    backend: str = "auto",
    concurrency: int = 20,
    max_retries: int = 3,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    http2: bool = True,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    timeout: float | None = None,
    cookies: dict[str, str] | None = None,
    random_user_agent: bool = True,
    random_proxy: bool = False,
    debug: bool = False,
    verbose: bool = True,
    return_none_on_failure: bool = False,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: Any = None,
    json: Any = None,
    headers: dict[str, str] | None = None,
    proxy: str | None = None,
    return_type: ReturnType | str = ReturnType.JSON,
    parse_func: Callable[[Any], Any] | None = None,
    keys: list[str] | None = None,
) -> Any:
    """Synchronous convenience function for parallel requests.

    This is the easiest way to make parallel requests. Uses asyncio.run() internally.

    Example:
        >>> from parallel_requests import parallel_requests
        >>> results = parallel_requests(
        ...     urls=["https://api.github.com/repos/python/cpython"],
        ...     concurrency=3,
        ... )
        >>> print(results[0]["name"])
        'cpython'

    Args:
        urls: Single URL or list of URLs to request
        backend: Backend to use ("auto", "niquests", "aiohttp", or "requests")
        concurrency: Maximum number of concurrent requests
        max_retries: Maximum retry attempts per request
        rate_limit: Requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2: Enable HTTP/2 (if supported by backend)
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
        timeout: Default timeout per request (seconds)
        cookies: Initial session cookies
        random_user_agent: Rotate user agents
        random_proxy: Enable proxy rotation
        debug: Enable debug logging
        verbose: Enable verbose output
        return_none_on_failure: Return None instead of raising on failure
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        headers: Request headers
        proxy: Proxy URL
        return_type: How to parse the response (json, text, content, response, stream)
        parse_func: Custom function to parse each response
        keys: Keys for dict return (must match urls length)

    Returns:
        - Single URL: single result
        - List of URLs: list of results
        - List of URLs with keys: dict mapping keys to results
    """

    async def _run() -> Any:
        client = ParallelRequests(
            backend=backend,
            concurrency=concurrency,
            max_retries=max_retries,
            rate_limit=rate_limit,
            rate_limit_burst=rate_limit_burst,
            http2=http2,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
            timeout=timeout,
            cookies=cookies,
            random_user_agent=random_user_agent,
            random_proxy=random_proxy,
            debug=debug,
            verbose=verbose,
            return_none_on_failure=return_none_on_failure,
        )
        async with client:
            return await client.request(
                urls,
                method=method,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout,
                proxy=proxy,
                return_type=return_type,
                parse_func=parse_func,
                keys=keys,
            )

    return asyncio.run(_run())


async def parallel_requests_async(
    urls: str | list[str],
    *,
    backend: str = "auto",
    concurrency: int = 20,
    max_retries: int = 3,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    http2: bool = True,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    timeout: float | None = None,
    cookies: dict[str, str] | None = None,
    random_user_agent: bool = True,
    random_proxy: bool = False,
    debug: bool = False,
    verbose: bool = True,
    return_none_on_failure: bool = False,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: Any = None,
    json: Any = None,
    headers: dict[str, str] | None = None,
    proxy: str | None = None,
    return_type: ReturnType | str = ReturnType.JSON,
    parse_func: Callable[[Any], Any] | None = None,
    keys: list[str] | None = None,
) -> Any:
    """Async convenience function for parallel requests.

    Example:
        >>> import asyncio
        >>> from parallel_requests import parallel_requests_async
        >>> async def main():
        ...     results = await parallel_requests_async(
        ...         urls=["https://httpbin.org/get"] * 3,
        ...         concurrency=5,
        ...     )
        ...     return results
        >>> results = asyncio.run(main())
        >>> print(len(results))
        3

    Args:
        urls: Single URL or list of URLs to request
        backend: Backend to use ("auto", "niquests", "aiohttp", or "requests")
        concurrency: Maximum number of concurrent requests
        max_retries: Maximum retry attempts per request
        rate_limit: Requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2: Enable HTTP/2 (if supported by backend)
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
        timeout: Default timeout per request (seconds)
        cookies: Initial session cookies
        random_user_agent: Rotate user agents
        random_proxy: Enable proxy rotation
        debug: Enable debug logging
        verbose: Enable verbose output
        return_none_on_failure: Return None instead of raising on failure
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        headers: Request headers
        proxy: Proxy URL
        return_type: How to parse the response (json, text, content, response, stream)
        parse_func: Custom function to parse each response
        keys: Keys for dict return (must match urls length)

    Returns:
        - Single URL: single result
        - List of URLs: list of results
        - List of URLs with keys: dict mapping keys to results
    """
    client = ParallelRequests(
        backend=backend,
        concurrency=concurrency,
        max_retries=max_retries,
        rate_limit=rate_limit,
        rate_limit_burst=rate_limit_burst,
        http2=http2,
        follow_redirects=follow_redirects,
        verify_ssl=verify_ssl,
        timeout=timeout,
        cookies=cookies,
        random_user_agent=random_user_agent,
        random_proxy=random_proxy,
        debug=debug,
        verbose=verbose,
        return_none_on_failure=return_none_on_failure,
    )
    async with client:
        return await client.request(
            urls,
            method=method,
            params=params,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
            proxy=proxy,
            return_type=return_type,
            parse_func=parse_func,
            keys=keys,
        )
