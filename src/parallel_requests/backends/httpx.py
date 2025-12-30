from typing import Any

import httpx

from parallel_requests.backends.base import Backend, NormalizedResponse, RequestConfig
from parallel_requests.exceptions import BackendError


class HttpxBackend(Backend):
    def __init__(self, http2_enabled: bool = True) -> None:
        super().__init__(http2_enabled=http2_enabled)
        self._client: httpx.AsyncClient | None = None
        self._h2_available: bool = False
        self._verify_ssl: bool = True

    @property
    def name(self) -> str:
        return "httpx"

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        if self._client is None:
            raise RuntimeError("Backend not initialized. Use async with HttpxBackend() as backend:")

        kwargs: dict[str, Any] = {
            "method": config.method,
            "url": config.url,
            "params": config.params,
            "headers": config.headers,
            "cookies": config.cookies,
            "timeout": config.timeout,
            "follow_redirects": config.follow_redirects,
        }

        if config.data is not None:
            kwargs["content"] = config.data

        if config.json is not None:
            kwargs["json"] = config.json

        if config.proxy is not None:
            kwargs["proxies"] = {"http": config.proxy, "https": config.proxy}

        try:
            if config.stream:
                async with self._client.stream(**kwargs) as response:
                    headers: dict[str, str] = {}
                    for key, value in response.headers.items():
                        headers[key] = value

                    content = await response.aread()

                    content_type = response.headers.get("content-type", "").lower()
                    is_json = "application/json" in content_type

                    return NormalizedResponse.from_backend(
                        status_code=response.status_code,
                        headers=headers,
                        content=content,
                        url=str(response.url),
                        is_json=is_json,
                    )
            else:
                response = await self._client.request(**kwargs)

                headers = {}
                for key, value in response.headers.items():
                    headers[key] = value

                content = response.content

                content_type = response.headers.get("content-type", "").lower()
                is_json = "application/json" in content_type

                return NormalizedResponse.from_backend(
                    status_code=response.status_code,
                    headers=headers,
                    content=content,
                    url=str(response.url),
                    is_json=is_json,
                )
        except httpx.HTTPError as e:
            raise BackendError(f"Request failed: {e}", backend_name=self.name) from e

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "HttpxBackend":
        limits = httpx.Limits(max_keepalive_connections=None, max_connections=None)
        self._h2_available = self._check_h2_available()
        http2 = self._http2_enabled and self._h2_available
        self._client = httpx.AsyncClient(http2=http2, limits=limits)
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def _check_h2_available(self) -> bool:
        try:
            import h2  # noqa

            return True
        except ImportError:
            return False

    def supports_http2(self) -> bool:
        """Return True if backend supports HTTP/2.

        Httpx supports HTTP/2 when http2_enabled=True and the h2 extra is installed.
        Without h2, httpx will fallback to HTTP/1.1.
        """
        if not self._http2_enabled:
            return False
        if not self._h2_available:
            self._h2_available = self._check_h2_available()
        return self._h2_available
