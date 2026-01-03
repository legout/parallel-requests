import pytest
import warnings

from fastreq.backends.aiohttp import AiohttpBackend
from fastreq.backends.base import RequestConfig
from fastreq.exceptions import BackendError


@pytest.mark.asyncio
async def test_aiohttp_backend_exception_wrapping():
    """Test that backend exceptions are properly wrapped in BackendError."""
    async with AiohttpBackend() as backend:
        # Use an invalid URL to trigger an error
        config = RequestConfig(
            url="http://invalid-domain-that-does-not-exist-12345.com", method="GET", timeout=1.0
        )

        with pytest.raises(BackendError) as exc_info:
            await backend.request(config)

        # Check that error is properly wrapped
        assert exc_info.value.backend_name == "aiohttp"
        assert "Request failed" in str(exc_info.value)
        # Check that original exception is chained
        assert exc_info.value.__cause__ is not None


@pytest.mark.asyncio
async def test_aiohttp_http2_warning_with_enabled():
    """Test that HTTP/2 warning is issued when enabled for aiohttp."""
    async with AiohttpBackend(http2_enabled=True) as backend:
        config = RequestConfig(url="https://httpbin.org/get", method="GET")

        with pytest.warns(UserWarning, match="does not support HTTP/2"):
            response = await backend.request(config)

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_aiohttp_http2_no_warning_with_disabled():
    """Test that no HTTP/2 warning is issued when disabled for aiohttp."""
    async with AiohttpBackend(http2_enabled=False) as backend:
        config = RequestConfig(url="https://httpbin.org/get", method="GET")

        # Use warnings module to capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            response = await backend.request(config)

        # No warnings should be captured
        http2_warnings = [w for w in warning_list if "HTTP/2" in str(w.message)]
        assert len(http2_warnings) == 0
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_aiohttp_http2_warning_only_once():
    """Test that HTTP/2 warning is only issued once per session."""
    async with AiohttpBackend(http2_enabled=True) as backend:
        config1 = RequestConfig(url="https://httpbin.org/get", method="GET")
        config2 = RequestConfig(url="https://httpbin.org/headers", method="GET")

        # First request should trigger warning
        with pytest.warns(UserWarning, match="does not support HTTP/2"):
            response1 = await backend.request(config1)

        # Second request should NOT trigger another warning
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            response2 = await backend.request(config2)

        # Check that no HTTP/2 warning was raised on second request
        http2_warnings = [w for w in warning_list if "HTTP/2" in str(w.message)]
        assert len(http2_warnings) == 0

        assert response1.status_code == 200
        assert response2.status_code == 200


@pytest.mark.asyncio
async def test_aiohttp_connection_error():
    """Test that connection errors are properly wrapped."""
    async with AiohttpBackend() as backend:
        # Use a non-routable IP to trigger connection error
        config = RequestConfig(url="http://192.0.2.1:1", method="GET", timeout=1.0)

        with pytest.raises(BackendError) as exc_info:
            await backend.request(config)

        assert exc_info.value.backend_name == "aiohttp"
        assert "Request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_aiohttp_timeout_error():
    """Test that timeout errors are properly wrapped."""
    async with AiohttpBackend() as backend:
        # Use a long delay with short timeout
        config = RequestConfig(url="https://httpbin.org/delay/10", method="GET", timeout=0.1)

        with pytest.raises(BackendError) as exc_info:
            await backend.request(config)

        assert exc_info.value.backend_name == "aiohttp"
        assert "Request failed" in str(exc_info.value)
