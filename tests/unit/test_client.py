from unittest.mock import AsyncMock, patch

import pytest

from parallel_requests import (
    ParallelRequests,
    RequestOptions,
    ReturnType,
    parallel_requests,
    parallel_requests_async,
)
from parallel_requests.exceptions import ConfigurationError


class TestParallelRequestsInit:
    @pytest.mark.asyncio
    async def test_init_with_defaults(self) -> None:
        client = ParallelRequests()
        assert client.backend_name == "auto"
        assert client.concurrency == 20
        assert client.follow_redirects is True
        assert client.verify_ssl is True
        assert client.random_user_agent is True
        assert client.random_proxy is False
        assert client.debug is False
        assert client.verbose is True
        assert client.return_none_on_failure is False

    @pytest.mark.asyncio
    async def test_init_with_custom_values(self) -> None:
        client = ParallelRequests(
            concurrency=10,
            http2=False,
        )
        assert client.concurrency == 10
        assert client._http2 is False

    @pytest.mark.asyncio
    async def test_init_with_cookies(self) -> None:
        client = ParallelRequests(cookies={"session": "abc123"})
        assert client._cookies == {"session": "abc123"}

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


class TestParallelRequestsRequest:
    @pytest.mark.asyncio
    async def test_single_url_returns_single_result(self) -> None:
        with patch("parallel_requests.client.ParallelRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"result": "success"}

            client = ParallelRequests()
            async with client:
                result = await client.request("https://example.com/api")

            # Single URL returns single result, not a list
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_multiple_urls_returns_list(self) -> None:
        with patch("parallel_requests.client.ParallelRequests._execute_request") as mock_exec:
            mock_exec.side_effect = [{"result": "a"}, {"result": "b"}]

            client = ParallelRequests()
            async with client:
                results = await client.request(["https://a.com", "https://b.com"])

            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0] == {"result": "a"}
            assert results[1] == {"result": "b"}

    @pytest.mark.asyncio
    async def test_urls_with_keys_returns_dict(self) -> None:
        with patch("parallel_requests.client.ParallelRequests._execute_request") as mock_exec:
            mock_exec.side_effect = [{"result": "first"}, {"result": "second"}]

            client = ParallelRequests()
            async with client:
                results = await client.request(
                    ["https://a.com", "https://b.com"],
                    keys=["first", "second"],
                )

            assert isinstance(results, dict)
            assert results["first"] == {"result": "first"}
            assert results["second"] == {"result": "second"}

    @pytest.mark.asyncio
    async def test_keys_mismatch_raises_error(self) -> None:
        client = ParallelRequests()
        async with client:
            with pytest.raises(ConfigurationError) as exc_info:
                await client.request(
                    ["https://a.com", "https://b.com"],
                    keys=["only_one"],
                )
            assert "Number of keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_func_applied(self) -> None:
        with patch("parallel_requests.client.ParallelRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"id": 123, "name": "test"}

            client = ParallelRequests()
            async with client:
                result = await client.request(
                    "https://example.com/api",
                    parse_func=lambda r: r.get("id"),
                )

            assert result == 123


class TestParallelRequestsAsyncFunctions:
    @pytest.mark.asyncio
    async def test_parallel_requests_async_wrapper(self) -> None:
        with patch("parallel_requests.client.ParallelRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            results = await parallel_requests_async(["https://example.com/api"])

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

            results = await parallel_requests_async(
                ["https://example.com/api"],
                backend="custom",
                concurrency=5,
                max_retries=10,
                rate_limit=50.0,
            )

            MockClient.assert_called_once()
            call_kwargs = MockClient.call_args[1]
            assert call_kwargs["backend"] == "custom"
            assert call_kwargs["concurrency"] == 5
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

                results = parallel_requests(["https://example.com/api"])

                assert len(results) == 1
                assert results[0] == {"result": "success"}
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_requests_async_single_url(self) -> None:
        with patch("parallel_requests.client.ParallelRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value={"result": "success"})
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = await parallel_requests_async("https://example.com/api")

            # Single URL returns single result
            assert result == {"result": "success"}
