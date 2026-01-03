import asyncio
import warnings
from typing import Any

import aiohttp

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig
from fastreq.exceptions import BackendError


class AiohttpBackend(Backend):
    def __init__(self, http2_enabled: bool = True) -> None:
        super().__init__(http2_enabled=http2_enabled)
        self._session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        return "aiohttp"

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        if self._session is None:
            raise RuntimeError(
                "Backend not initialized. Use async with AiohttpBackend() as backend:"
            )

        if self._http2_enabled and not self._http2_warned:
            warnings.warn(
                f"Backend '{self.name}' does not support HTTP/2. "
                "The http2 configuration will be ignored.",
                UserWarning,
                stacklevel=2,
            )
            self._http2_warned = True

        kwargs: dict[str, Any] = {
            "headers": config.headers,
            "cookies": config.cookies,
        }

        if config.timeout is not None:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=config.timeout)

        if config.data is not None:
            kwargs["data"] = config.data

        if config.json is not None:
            kwargs["json"] = config.json

        if config.params is not None:
            kwargs["params"] = config.params

        if config.proxy is not None:
            kwargs["proxy"] = config.proxy

        try:
            response = await self._session.request(
                method=config.method,
                url=config.url,
                **kwargs,
            )
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise BackendError(f"Request failed: {e}", backend_name=self.name) from e

        headers: dict[str, str] = {}
        for key, value in response.headers.items():
            headers[key] = value

        content = await response.read()

        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type

        return NormalizedResponse.from_backend(
            status_code=response.status,
            headers=headers,
            content=content,
            url=str(response.url),
            is_json=is_json,
        )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "AiohttpBackend":
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        """Return True if backend supports HTTP/2.

        aiohttp does not natively support HTTP/2. External extensions like
        aiohttp-h2 may provide support but are not part of the core library.
        """
        return False
