import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from parallel_requests import (
    ParallelRequests,
    RequestOptions,
    ReturnType,
    parallel_requests,
    parallel_requests_async,
)
from parallel_requests.backends.base import NormalizedResponse
from parallel_requests.exceptions import ConfigurationError, PartialFailureError


class TestParallelRequestsInit:
    @pytest.mark.asyncio
    async def test_init_with_defaults(self) -> None:
        client = ParallelRequests()
        assert client.backend_name == "auto"
        assert client.max_concurrency == 20
        assert client.allow_redirects is True
        assert client.verify_ssl is True
        assert client.debug is False
        assert client.verbose is True
        assert client.return_none_on_failure is False

    @pytest.mark.asyncio
    async def test_init_with_custom_values(self) -> None:
        client = ParallelRequests(
            max_concurrency=10,
            http2_enabled=False,
        )
        assert client.max_concurrency == 10
        assert client._http2_enabled is False

    @pytest.mark.asyncio
    async def test_reset_cookies(self) -> None:
        client = ParallelRequests()
        client._cookies = {"session_id": "123"}

        client.reset_cookies()
        assert client._cookies == {}

    @pytest.mark.asyncio
    async def test_set_cookies(self) -> None:
        client = ParallelRequests()

        client.set_cookies({"session_id": "123"})
        assert client._cookies == {"session_id": "123"}

        client.set_cookies({"user_id": "456"})
        assert client._cookies == {"session_id": "123", "user_id": "456"}

    @pytest.mark.asyncio
    async def test_backend_selection_no_backend_found(self) -> None:
        with patch("parallel_requests.client.importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("No backend found")

            with pytest.raises(ConfigurationError) as exc_info:
                ParallelRequests()

            assert "No suitable backend found" in str(exc_info.value)


class TestRequestOptions:
    def test_default_values(self) -> None:
        opts = RequestOptions(url="https://example.com")
        assert opts.url == "https://example.com"
        assert opts.method == "GET"
        assert opts.params is None
        assert opts.data is None
        assert opts.json is None
        assert opts.headers is None
        assert opts.timeout is None
        assert opts.proxy is None
        assert opts.return_type == ReturnType.JSON
        assert opts.stream_callback is None

    def test_custom_values(self) -> None:
        opts = RequestOptions(
            url="https://example.com",
            method="POST",
            params={"key": "value"},
            json={"data": "test"},
            headers={"Authorization": "Bearer token"},
            timeout=30.0,
            proxy="http://proxy.example.com:8080",
            return_type=ReturnType.TEXT,
        )
        assert opts.method == "POST"
        assert opts.params == {"key": "value"}
        assert opts.json == {"data": "test"}
        assert opts.headers == {"Authorization": "Bearer token"}
        assert opts.timeout == 30.0
        assert opts.proxy == "http://proxy.example.com:8080"
        assert opts.return_type == ReturnType.TEXT


class TestReturnType:
    def test_json_value(self) -> None:
        assert ReturnType.JSON.value == "json"

    def test_text_value(self) -> None:
        assert ReturnType.TEXT.value == "text"

    def test_content_value(self) -> None:
        assert ReturnType.CONTENT.value == "content"

    def test_response_value(self) -> None:
        assert ReturnType.RESPONSE.value == "response"

    def test_stream_value(self) -> None:
        assert ReturnType.STREAM.value == "stream"


class TestParallelRequestsAsyncFunctions:
    @pytest.mark.asyncio
    async def test_parallel_requests_async_wrapper(self) -> None:
        with patch("parallel_requests.client.ParallelRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            request = RequestOptions(url="https://example.com/api")

            results = await parallel_requests_async([request])

            assert len(results) == 1
            assert results[0] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_parallel_requests_async_with_custom_config(self) -> None:
        with patch("parallel_requests.client.ParallelRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            request = RequestOptions(url="https://example.com/api")

            results = await parallel_requests_async(
                [request],
                backend="custom",
                max_concurrency=5,
                max_retries=10,
                rate_limit=50.0,
            )

            MockClient.assert_called_once()
            call_kwargs = MockClient.call_args[1]
            assert call_kwargs["backend"] == "custom"
            assert call_kwargs["max_concurrency"] == 5
            assert call_kwargs["rate_limit"] == 50.0
            assert len(results) == 1

    def test_parallel_requests_sync_wrapper(self) -> None:
        with patch("parallel_requests.client.ParallelRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            with patch("parallel_requests.client.asyncio.run") as mock_run:
                mock_run.return_value = [{"result": "success"}]

                request = RequestOptions(url="https://example.com/api")

                results = parallel_requests([request])

                assert len(results) == 1
                assert results[0] == {"result": "success"}
                mock_run.assert_called_once()
