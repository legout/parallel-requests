import pytest
import warnings

from fastreq.backends.niquests import NiquestsBackend
from fastreq.backends.base import RequestConfig
from fastreq.exceptions import BackendError


@pytest.mark.asyncio
async def test_niquests_backend_exception_wrapping():
    """Test that backend exceptions are properly wrapped in BackendError."""
    async with NiquestsBackend() as backend:
        # Use an invalid URL to trigger an error
        config = RequestConfig(
            url="http://invalid-domain-that-does-not-exist-12345.com", method="GET", timeout=1.0
        )

        with pytest.raises(BackendError) as exc_info:
            await backend.request(config)

        # Check that error is properly wrapped
        assert exc_info.value.backend_name == "niquests"
        assert "Request failed" in str(exc_info.value)
        # Check that original exception is chained
        assert exc_info.value.__cause__ is not None


@pytest.mark.asyncio
async def test_niquests_http2_no_warning_with_enabled():
    """Test that no HTTP/2 warning is issued when enabled for niquests (supports HTTP/2)."""
    async with NiquestsBackend(http2_enabled=True) as backend:
        config = RequestConfig(url="https://httpbin.org/get", method="GET")

        # Use warnings module to capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            response = await backend.request(config)

        # No HTTP/2 warnings should be raised for niquests
        http2_warnings = [w for w in warning_list if "HTTP/2" in str(w.message)]
        assert len(http2_warnings) == 0
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_niquests_http2_no_warning_with_disabled():
    """Test that no HTTP/2 warning is issued when disabled for niquests."""
    async with NiquestsBackend(http2_enabled=False) as backend:
        config = RequestConfig(url="https://httpbin.org/get", method="GET")

        # Use warnings module to capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")
            response = await backend.request(config)

        # No warnings should be captured
        assert len([w for w in warning_list if "HTTP/2" in str(w.message)]) == 0
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_niquets_connection_error():
    """Test that connection errors are properly wrapped."""
    async with NiquestsBackend() as backend:
        # Use a non-routable IP to trigger connection error
        config = RequestConfig(url="http://192.0.2.1:1", method="GET", timeout=1.0)

        with pytest.raises(BackendError) as exc_info:
            await backend.request(config)

        assert exc_info.value.backend_name == "niquests"
        assert "Request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_niquests_timeout_error():
    """Test that timeout errors are properly wrapped."""
    async with NiquestsBackend() as backend:
        # Use a long delay with short timeout
        config = RequestConfig(url="https://httpbin.org/delay/10", method="GET", timeout=0.1)

        with pytest.raises(BackendError) as exc_info:
            await backend.request(config)

        assert exc_info.value.backend_name == "niquests"
        assert "Request failed" in str(exc_info.value)
