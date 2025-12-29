from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class RequestConfig:
    url: str
    method: str = "GET"
    params: dict[str, Any] | None = None
    data: Any = None
    json: Any = None
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    timeout: float | None = None
    proxy: str | None = None
    http2: bool = True
    stream: bool = False


@dataclass
class NormalizedResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    json_data: Any
    url: str
    is_json: bool = False

    def __post_init__(self) -> None:
        if self.is_json and self.json_data is None:
            import json

            try:
                self.json_data = json.loads(self.text)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    @staticmethod
    def _normalize_headers(headers: Mapping[str, str] | dict[str, str]) -> dict[str, str]:
        """Normalize headers by converting all keys to lowercase."""
        return {key.lower(): value for key, value in headers.items()}

    @classmethod
    def from_backend(
        cls,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
        url: str,
        is_json: bool = False,
    ) -> "NormalizedResponse":
        text = content.decode("utf-8", errors="replace")
        normalized_headers = cls._normalize_headers(headers)
        return cls(
            status_code=status_code,
            headers=normalized_headers,
            content=content,
            text=text,
            json_data=None,
            url=url,
            is_json=is_json,
        )


class Backend(ABC):
    def __init__(self, http2_enabled: bool = True) -> None:
        """Initialize backend with HTTP/2 configuration.

        Args:
            http2_enabled: Whether HTTP/2 should be enabled if supported by backend.
                          Ignored by backends that don't support HTTP/2.
        """
        self._http2_enabled = http2_enabled
        self._http2_warned = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend identifier."""
        ...

    @abstractmethod
    async def request(self, config: RequestConfig) -> NormalizedResponse:
        """Execute an HTTP request and return a normalized response."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up backend resources."""
        ...

    @abstractmethod
    async def __aenter__(self) -> "Backend":
        """Enter context manager."""
        ...

    @abstractmethod
    async def __aexit__(self, *args: Any) -> None:
        """Exit context manager."""
        ...

    @abstractmethod
    def supports_http2(self) -> bool:
        """Return True if backend supports HTTP/2."""
        ...
