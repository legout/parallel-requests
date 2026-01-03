from typing import Any

import niquests

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig
from fastreq.exceptions import BackendError


class NiquestsBackend(Backend):
    def __init__(self, http2_enabled: bool = True) -> None:
        super().__init__(http2_enabled=http2_enabled)
        self._session: niquests.AsyncSession | None = None

    @property
    def name(self) -> str:
        return "niquests"

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        if self._session is None:
            raise RuntimeError(
                "Backend not initialized. Use async with NiquestsBackend() as backend:"
            )

        kwargs: dict[str, Any] = {
            "method": config.method,
            "url": config.url,
            "params": config.params,
            "headers": config.headers,
            "cookies": config.cookies,
            "timeout": config.timeout,
        }

        if config.data is not None:
            kwargs["data"] = config.data

        if config.json is not None:
            kwargs["json"] = config.json

        if config.proxy is not None:
            kwargs["proxies"] = {"http": config.proxy, "https": config.proxy}

        kwargs["stream"] = config.stream

        try:
            response = await self._session.request(**kwargs)
        except niquests.RequestException as e:
            raise BackendError(f"Request failed: {e}", backend_name=self.name) from e

        headers: dict[str, str] = {}
        for key, value in response.headers.items():
            headers[key] = value

        if config.stream:
            content = await response.content
        else:
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

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "NiquestsBackend":
        self._session = niquests.AsyncSession(disable_http2=not self._http2_enabled)
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        """Return True if backend supports HTTP/2.

        Niquests supports HTTP/2 by default and can be controlled via
        the http2_enabled parameter.
        """
        return True
