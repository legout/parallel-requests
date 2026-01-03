from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class RequestConfig:
    """Configuration for a single HTTP request.

    Used internally by backends to normalize request parameters.

    Attributes:
        url: Request URL
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        headers: Request headers
        cookies: Request cookies
        timeout: Per-request timeout in seconds
        proxy: Proxy URL
        http2: Enable HTTP/2
        stream: Enable streaming mode
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
    """

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
    follow_redirects: bool = True
    verify_ssl: bool = True


@dataclass
class NormalizedResponse:
    """Normalized response from HTTP backends.

    Provides a consistent interface across different backend implementations.

    Attributes:
        status_code: HTTP status code
        headers: Response headers (normalized to lowercase)
        content: Raw response body as bytes
        text: Decoded response body as string
        json_data: Parsed JSON data (if applicable)
        url: Final URL (after redirects)
        is_json: Whether response contains valid JSON
    """

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
        """Normalize headers by converting all keys to lowercase.

        Args:
            headers: Original headers dictionary

        Returns:
            Headers with all keys lowercase
        """
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
        """Create NormalizedResponse from backend response.

        Args:
            status_code: HTTP status code
            headers: Response headers
            content: Response content as bytes
            url: Final URL
            is_json: Whether response is JSON

        Returns:
            NormalizedResponse instance
        """
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
    """Abstract base class for HTTP backends.

    All backends must implement this interface to provide a consistent
    experience across different HTTP client libraries.

    Example:
        >>> class CustomBackend(Backend):
        ...     @property
        ...     def name(self) -> str:
        ...         return "custom"
        ...
        ...     async def request(self, config: RequestConfig) -> NormalizedResponse:
        ...         # Implementation
        ...         pass
        ...
        ...     async def close(self) -> None:
        ...         # Cleanup
        ...         pass
        ...
        ...     async def __aenter__(self) -> "Backend":
        ...         return self
        ...
        ...     async def __aexit__(self, *args: Any) -> None:
        ...         await self.close()
        ...
        ...     def supports_http2(self) -> bool:
        ...         return False
    """

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
        """Return the backend identifier.

        Returns:
            Backend name string (e.g., "niquests", "aiohttp", "requests")
        """
        ...

    @abstractmethod
    async def request(self, config: RequestConfig) -> NormalizedResponse:
        """Execute an HTTP request and return a normalized response.

        Args:
            config: Request configuration

        Returns:
            NormalizedResponse with status, headers, and content
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up backend resources.

        Called when closing the client or exiting context manager.
        """
        ...

    @abstractmethod
    async def __aenter__(self) -> "Backend":
        """Enter context manager and initialize backend session.

        Returns:
            Self for use in async with statement
        """
        ...

    @abstractmethod
    async def __aexit__(self, *args: Any) -> None:
        """Exit context manager and cleanup resources."""
        ...

    @abstractmethod
    def supports_http2(self) -> bool:
        """Return True if backend supports HTTP/2.

        Returns:
            True if HTTP/2 is supported, False otherwise
        """
        ...
