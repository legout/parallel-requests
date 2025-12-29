import asyncio
import warnings
from typing import Any

import requests

from parallel_requests.backends.base import Backend, NormalizedResponse, RequestConfig
from parallel_requests.exceptions import BackendError


class RequestsBackend(Backend):
    def __init__(self, http2_enabled: bool = True) -> None:
        super().__init__(http2_enabled=http2_enabled)
        self._session: requests.Session | None = None

    @property
    def name(self) -> str:
        return "requests"

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        if self._session is None:
            raise RuntimeError(
                "Backend not initialized. Use async with RequestsBackend() as backend:"
            )

        if self._http2_enabled and not self._http2_warned:
            warnings.warn(
                f"Backend '{self.name}' does not support HTTP/2. "
                "The http2 configuration will be ignored.",
                UserWarning,
                stacklevel=2,
            )
            self._http2_warned = True

        session = self._session

        def _make_request() -> requests.Response:
            return session.request(
                method=config.method,
                url=config.url,
                params=config.params,
                data=config.data,
                json=config.json,
                headers=config.headers,
                cookies=config.cookies,
                timeout=config.timeout,
                proxies={"http": config.proxy, "https": config.proxy} if config.proxy else None,
                stream=config.stream,
            )

        try:
            response = await asyncio.to_thread(_make_request)
        except requests.RequestException as e:
            raise BackendError(f"Request failed: {e}", backend_name=self.name) from e

        headers: dict[str, str] = {}
        for key, value in response.headers.items():
            headers[key] = value

        content = response.content

        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type

        return NormalizedResponse.from_backend(
            status_code=response.status_code,
            headers=headers,
            content=content,
            url=response.url,
            is_json=is_json,
        )

    async def close(self) -> None:
        if self._session is not None:
            session = self._session
            self._session = None
            await asyncio.to_thread(session.close)

    async def __aenter__(self) -> "RequestsBackend":
        self._session = requests.Session()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        """Return True if backend supports HTTP/2.

        requests does not support HTTP/2. For HTTP/2 support, use niquests backend.
        """
        return False
