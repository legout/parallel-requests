import asyncio
import importlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .backends.base import Backend, RequestConfig, NormalizedResponse
from .exceptions import (
    ConfigurationError,
    FailureDetails,
    PartialFailureError,
)
from .utils.rate_limiter import AsyncRateLimiter, RateLimitConfig
from .utils.retry import RetryConfig, RetryStrategy


class ReturnType(str, Enum):
    JSON = "json"
    TEXT = "text"
    CONTENT = "content"
    RESPONSE = "response"
    STREAM = "stream"


@dataclass
class RequestOptions:
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


class ParallelRequests:
    def __init__(
        self,
        backend: str = "auto",
        max_concurrency: int = 20,
        max_retries: int = 3,
        rate_limit: float | None = None,
        rate_limit_burst: int = 5,
        http2_enabled: bool = True,
        allow_redirects: bool = True,
        verify_ssl: bool = True,
        debug: bool = False,
        verbose: bool = True,
        return_none_on_failure: bool = False,
    ) -> None:
        self.backend_name = backend
        self.max_concurrency = max_concurrency
        self.allow_redirects = allow_redirects
        self.verify_ssl = verify_ssl
        self.debug = debug
        self.verbose = verbose
        self.return_none_on_failure = return_none_on_failure

        self._backend: Backend | None = None
        self._cookies: dict[str, str] = {}
        self._rate_limiter: AsyncRateLimiter | None = None

        retry_config = RetryConfig(max_retries=max_retries)
        self._retry_strategy = RetryStrategy(retry_config)

        if rate_limit is not None:
            rate_limit_config = RateLimitConfig(
                requests_per_second=rate_limit,
                burst=rate_limit_burst,
                max_concurrency=max_concurrency,
            )
            self._rate_limiter = AsyncRateLimiter(rate_limit_config)

        self._http2_enabled = http2_enabled
        self._select_backend()

    def _select_backend(self) -> None:
        if self.backend_name == "auto":
            backend_classes = [
                ("niquests", "NiquestsBackend"),
                ("aiohttp", "AiohttpBackend"),
                ("requests", "RequestsBackend"),
            ]

            for backend_module, backend_class_name in backend_classes:
                try:
                    module = importlib.import_module(f"parallel_requests.backends.{backend_module}")
                    backend_cls = getattr(module, backend_class_name)
                    self._backend = backend_cls(http2_enabled=self._http2_enabled)
                    return
                except ImportError:
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
                self._backend = backend_cls(http2_enabled=self._http2_enabled)
            except ImportError as e:
                raise ConfigurationError(f"Failed to load backend '{self.backend_name}': {e}")

    async def __aenter__(self) -> "ParallelRequests":
        if self._backend:
            await self._backend.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._backend:
            await self._backend.__aexit__(*args)

    async def close(self) -> None:
        if self._backend:
            await self._backend.close()

    def reset_cookies(self) -> None:
        self._cookies = {}

    def set_cookies(self, cookies: dict[str, str]) -> None:
        self._cookies.update(cookies)

    async def request(self, requests: list[RequestOptions]) -> list[Any]:
        if not self._backend:
            raise ConfigurationError("Backend not initialized")

        tasks = [self._execute_request(req) for req in requests]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures: dict[str, FailureDetails] = {}
        processed_results: list[Any] = []

        for idx, result in enumerate(results):
            url = requests[idx].url

            if isinstance(result, Exception):
                if self.return_none_on_failure:
                    processed_results.append(None)
                else:
                    failures[url] = FailureDetails(url=url, error=result)
                    processed_results.append(result)
            else:
                processed_results.append(result)

        if failures and not self.return_none_on_failure:
            raise PartialFailureError(
                f"Partial failure: {len(failures)} of {len(requests)} requests failed",
                failures=failures,
                successes=len([r for r in results if not isinstance(r, Exception)]),
                total=len(requests),
            )

        return processed_results

    async def _execute_request(self, req: RequestOptions) -> Any:
        if not self._backend:
            raise ConfigurationError("Backend not initialized")

        backend = self._backend

        async def make_request() -> NormalizedResponse:
            async with self._rate_limiter.acquire() if self._rate_limiter else AsyncExit():
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
                        http2=self._http2_enabled,
                        stream=req.return_type == ReturnType.STREAM,
                    )
                )

        response = await self._retry_strategy.execute(make_request)
        return self._parse_response(response, req)

    def _parse_response(self, response: NormalizedResponse, req: RequestOptions) -> Any:
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


class AsyncExit:
    async def __aenter__(self) -> "AsyncExit":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


def parallel_requests(
    requests: list[RequestOptions],
    backend: str = "auto",
    max_concurrency: int = 20,
    max_retries: int = 3,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    http2_enabled: bool = True,
    allow_redirects: bool = True,
    verify_ssl: bool = True,
    debug: bool = False,
    verbose: bool = True,
    return_none_on_failure: bool = False,
) -> list[Any]:
    async def _run() -> list[Any]:
        client = ParallelRequests(
            backend=backend,
            max_concurrency=max_concurrency,
            max_retries=max_retries,
            rate_limit=rate_limit,
            rate_limit_burst=rate_limit_burst,
            http2_enabled=http2_enabled,
            allow_redirects=allow_redirects,
            verify_ssl=verify_ssl,
            debug=debug,
            verbose=verbose,
            return_none_on_failure=return_none_on_failure,
        )
        async with client:
            return await client.request(requests)

    return asyncio.run(_run())


async def parallel_requests_async(
    requests: list[RequestOptions],
    backend: str = "auto",
    max_concurrency: int = 20,
    max_retries: int = 3,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    http2_enabled: bool = True,
    allow_redirects: bool = True,
    verify_ssl: bool = True,
    debug: bool = False,
    verbose: bool = True,
    return_none_on_failure: bool = False,
) -> list[Any]:
    client = ParallelRequests(
        backend=backend,
        max_concurrency=max_concurrency,
        max_retries=max_retries,
        rate_limit=rate_limit,
        rate_limit_burst=rate_limit_burst,
        http2_enabled=http2_enabled,
        allow_redirects=allow_redirects,
        verify_ssl=verify_ssl,
        debug=debug,
        verbose=verbose,
        return_none_on_failure=return_none_on_failure,
    )
    async with client:
        return await client.request(requests)
