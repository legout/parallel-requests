from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastreq import (
    FastRequests,
    RequestOptions,
    ReturnType,
    fastreq,
    fastreq_async,
)
from fastreq.backends.base import NormalizedResponse
from fastreq.exceptions import ConfigurationError


class TestFastRequestsInit:
    @pytest.mark.asyncio
    async def test_init_with_defaults(self) -> None:
        client = FastRequests()
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
        client = FastRequests(
            concurrency=10,
            http2=False,
        )
        assert client.concurrency == 10
        assert client._http2 is False

    @pytest.mark.asyncio
    async def test_init_with_rate_limit(self) -> None:
        client = FastRequests(
            rate_limit=100.0,
            rate_limit_burst=10,
            concurrency=5,
        )
        assert client._rate_limiter is not None

    @pytest.mark.asyncio
    async def test_init_without_rate_limit(self) -> None:
        client = FastRequests()
        assert client._rate_limiter is None

    @pytest.mark.asyncio
    async def test_init_with_cookies(self) -> None:
        client = FastRequests(cookies={"session": "abc123"})
        assert client._cookies == {"session": "abc123"}

    @pytest.mark.asyncio
    async def test_reset_cookies(self) -> None:
        client = FastRequests()
        client._cookies = {"session_id": "123"}

        client.reset_cookies()
        assert client._cookies == {}

    @pytest.mark.asyncio
    async def test_set_cookies(self) -> None:
        client = FastRequests()

        client.set_cookies({"session_id": "123"})
        assert client._cookies == {"session_id": "123"}

        client.set_cookies({"user_id": "456"})
        assert client._cookies == {"session_id": "123", "user_id": "456"}

    @pytest.mark.asyncio
    async def test_context_manager_entry(self) -> None:
        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_backend = AsyncMock()
            mock_backend.__aenter__ = AsyncMock(return_value=mock_backend)
            mock_backend.__aexit__ = AsyncMock(return_value=None)
            mock_module = MagicMock()
            mock_module.NiquestsBackend = MagicMock(return_value=mock_backend)
            mock_import.return_value = mock_module

            async with FastRequests() as client:
                assert client is not None
                mock_backend.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exit(self) -> None:
        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_backend = AsyncMock()
            mock_backend.__aenter__ = AsyncMock(return_value=mock_backend)
            mock_backend.__aexit__ = AsyncMock(return_value=None)
            mock_module = MagicMock()
            mock_module.NiquestsBackend = MagicMock(return_value=mock_backend)
            mock_import.return_value = mock_module

            async with FastRequests() as client:
                pass

            mock_backend.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method(self) -> None:
        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_backend = AsyncMock()
            mock_backend.close = AsyncMock(return_value=None)
            mock_module = MagicMock()
            mock_module.NiquestsBackend = MagicMock(return_value=mock_backend)
            mock_import.return_value = mock_module

            client = FastRequests()
            await client.close()

            mock_backend.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_backend_selection_no_backend_found(self) -> None:
        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("No backend found")

            with pytest.raises(ConfigurationError) as exc_info:
                FastRequests()

            assert "No suitable backend found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manual_backend_selection(self) -> None:
        from fastreq.backends.base import Backend

        class MockBackend(Backend):
            def __init__(self, http2_enabled: bool = True, concurrency: int | None = None):
                super().__init__(http2_enabled, concurrency)

            @property
            def name(self) -> str:
                return "requests"

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def close(self):
                pass

            async def request(self, config):
                pass

            def supports_http2(self):
                return True

        mock_backend = MockBackend()

        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.RequestsBackend = MockBackend
            mock_import.return_value = mock_module

            client = FastRequests(backend="requests")
            assert client._backend.name == "requests"

    @pytest.mark.asyncio
    async def test_manual_backend_not_found(self) -> None:
        class EmptyModule:
            __dict__ = {}

        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_import.return_value = EmptyModule()

            with pytest.raises(ConfigurationError) as exc_info:
                FastRequests(backend="requests")

            assert "Backend 'requests' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manual_backend_import_error(self) -> None:
        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            with pytest.raises(ConfigurationError) as exc_info:
                FastRequests(backend="nonexistent")

            assert "Failed to load backend 'nonexistent'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_explicit_httpx_backend_selection(self) -> None:
        from fastreq.backends.base import Backend

        class MockHttpxBackend(Backend):
            def __init__(self, http2_enabled: bool = True, concurrency: int | None = None):
                super().__init__(http2_enabled, concurrency)

            @property
            def name(self) -> str:
                return "httpx"

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def close(self):
                pass

            async def request(self, config):
                pass

            def supports_http2(self) -> bool:
                return True

        mock_backend = MockHttpxBackend()

        with patch("fastreq.client.importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.HttpxBackend = MockHttpxBackend
            mock_import.return_value = mock_module

            client = FastRequests(backend="httpx")
            assert client._backend.name == "httpx"

    @pytest.mark.asyncio
    async def test_auto_backend_selection_with_httpx_priority(self) -> None:
        with patch("fastreq.client.importlib.util.find_spec") as mock_find:
            with patch("fastreq.client.importlib.import_module") as mock_import:
                mock_backend = AsyncMock()
                mock_backend.__aenter__ = AsyncMock(return_value=mock_backend)
                mock_backend.__aexit__ = AsyncMock(return_value=None)

                mock_module = MagicMock()
                mock_module.NiquestsBackend = MagicMock(return_value=mock_backend)
                mock_import.return_value = mock_module
                mock_find.side_effect = lambda x: None if x == "niquests" else MagicMock()

                client = FastRequests()
                assert client._backend is not None


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


class TestFastRequestsRequest:
    @pytest.mark.asyncio
    async def test_single_url_returns_single_result(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"result": "success"}

            client = FastRequests()
            async with client:
                result = await client.request("https://example.com/api")

            # Single URL returns single result, not a list
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_multiple_urls_returns_list(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.side_effect = [{"result": "a"}, {"result": "b"}]

            client = FastRequests()
            async with client:
                results = await client.request(["https://a.com", "https://b.com"])

            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0] == {"result": "a"}
            assert results[1] == {"result": "b"}

    @pytest.mark.asyncio
    async def test_urls_with_keys_returns_dict(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.side_effect = [{"result": "first"}, {"result": "second"}]

            client = FastRequests()
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
        client = FastRequests()
        async with client:
            with pytest.raises(ConfigurationError) as exc_info:
                await client.request(
                    ["https://a.com", "https://b.com"],
                    keys=["only_one"],
                )
            assert "Number of keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_func_applied(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"id": 123, "name": "test"}

            client = FastRequests()
            async with client:
                result = await client.request(
                    "https://example.com/api",
                    parse_func=lambda r: r.get("id"),
                )

            assert result == 123

    @pytest.mark.asyncio
    async def test_return_none_on_failure(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.side_effect = [
                {"result": "success"},
                Exception("Connection failed"),
                {"result": "success"},
            ]

            client = FastRequests(return_none_on_failure=True)
            async with client:
                results = await client.request(["https://a.com", "https://b.com", "https://c.com"])

            assert len(results) == 3
            assert results[0] == {"result": "success"}
            assert results[1] is None
            assert results[2] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_partial_failure_error(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.side_effect = [
                {"result": "success"},
                Exception("Connection failed"),
                {"result": "success"},
            ]

            from fastreq.exceptions import PartialFailureError

            client = FastRequests(return_none_on_failure=False)
            async with client:
                with pytest.raises(PartialFailureError) as exc_info:
                    await client.request(["https://a.com", "https://b.com", "https://c.com"])

            assert "1 of 3 requests failed" in str(exc_info.value)
            assert "https://b.com" in exc_info.value.failures


class TestFastRequestsAsyncFunctions:
    @pytest.mark.asyncio
    async def test_fastreq_async_wrapper(self) -> None:
        with patch("fastreq.client.FastRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            results = await fastreq_async(["https://example.com/api"])

            assert len(results) == 1
            assert results[0] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_fastreq_async_with_custom_config(self) -> None:
        with patch("fastreq.client.FastRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            results = await fastreq_async(
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

    def test_fastreq_sync_wrapper(self) -> None:
        with patch("fastreq.client.FastRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=[{"result": "success"}])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            with patch("fastreq.client.asyncio.run") as mock_run:
                mock_run.return_value = [{"result": "success"}]

                results = fastreq(["https://example.com/api"])

                assert len(results) == 1
                assert results[0] == {"result": "success"}
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_fastreq_async_single_url(self) -> None:
        with patch("fastreq.client.FastRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value={"result": "success"})
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = await fastreq_async("https://example.com/api")

            # Single URL returns single result
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_return_type_as_string(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"data": "result"}

            client = FastRequests()
            async with client:
                result = await client.request(
                    "https://example.com/api",
                    return_type="json",
                )

            assert result == {"data": "result"}

    @pytest.mark.asyncio
    async def test_follow_redirects_override(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"status": "ok"}

            client = FastRequests(follow_redirects=False)
            async with client:
                await client.request(
                    "https://example.com",
                    follow_redirects=True,  # Override to True
                )

            # Verify override is passed to _execute_request
            call_kwargs = mock_exec.call_args[1]
            assert call_kwargs["follow_redirects"] is True

    @pytest.mark.asyncio
    async def test_verify_ssl_override(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"status": "ok"}

            client = FastRequests(verify_ssl=False)
            async with client:
                await client.request(
                    "https://example.com",
                    verify_ssl=True,  # Override to True
                )

            # Verify override is passed to _execute_request
            call_kwargs = mock_exec.call_args[1]
            assert call_kwargs["verify_ssl"] is True

    @pytest.mark.asyncio
    async def test_timeout_override(self) -> None:
        with patch("fastreq.client.FastRequests._execute_request") as mock_exec:
            mock_exec.return_value = {"status": "ok"}

            client = FastRequests(timeout=10.0)
            async with client:
                await client.request(
                    "https://example.com",
                    timeout=30.0,  # Override to 30s
                )

            # Verify override is passed to _execute_request
            req = mock_exec.call_args[0][0]
            assert req.timeout == 30.0

    @pytest.mark.asyncio
    async def test_stream_callback_invoked(self) -> None:
        chunks = []

        def callback(chunk: bytes) -> None:
            chunks.append(chunk)

        # Test that STREAM return_type with callback works
        # We'll test via RequestOptions which uses stream_callback internally

        mock_response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/zip"},
            content=b"chunk1chunk2chunk3",
            url="https://example.com/file.zip",
            is_json=False,
        )

        client = FastRequests()
        result = client._parse_response(
            mock_response,
            RequestOptions(
                url="https://example.com/file.zip",
                return_type=ReturnType.STREAM,
                stream_callback=callback,
            ),
        )

        # STREAM return type calls callback and returns None
        assert result is None
        assert chunks[0] == b"chunk1chunk2chunk3"

    @pytest.mark.asyncio
    async def test_parse_response_json(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b'{"key": "value"}',
            url="https://example.com",
            is_json=True,
        )

        client = FastRequests()
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.JSON),
        )
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_parse_response_text(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"hello world",
            url="https://example.com",
            is_json=False,
        )

        client = FastRequests()
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.TEXT),
        )
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_parse_response_content(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/octet-stream"},
            content=b"binary data",
            url="https://example.com",
            is_json=False,
        )

        client = FastRequests()
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.CONTENT),
        )
        assert result == b"binary data"

    @pytest.mark.asyncio
    async def test_parse_response_response(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"hello",
            url="https://example.com",
            is_json=False,
        )

        client = FastRequests()
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.RESPONSE),
        )
        assert result is response

    @pytest.mark.asyncio
    async def test_null_context(self) -> None:
        client = FastRequests()
        async with client._null_context():
            pass

    @pytest.mark.asyncio
    async def test_request_without_backend(self) -> None:
        client = FastRequests()
        client._backend = None

        with pytest.raises(ConfigurationError) as exc_info:
            async with client:
                await client.request("https://example.com")

        assert "Backend not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_request_without_backend(self) -> None:
        client = FastRequests()
        client._backend = None

        with pytest.raises(ConfigurationError) as exc_info:
            await client._execute_request(
                RequestOptions(url="https://example.com"),
                follow_redirects=True,
                verify_ssl=True,
            )

        assert "Backend not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_request_with_rate_limiter(self) -> None:
        from fastreq.backends.base import NormalizedResponse

        mock_response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b'{"result": "success"}',
            url="https://example.com",
            is_json=True,
        )

        client = FastRequests(rate_limit=10.0, rate_limit_burst=5)
        assert client._rate_limiter is not None

        with patch.object(client._backend, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            async with client:
                result = await client.request(
                    "https://example.com/api",
                    return_type=ReturnType.JSON,
                )

            assert result == {"result": "success"}

    def test_fastreq_sync_function(self) -> None:
        with patch("fastreq.client.FastRequests") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value={"result": "sync"})
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            result = fastreq(
                ["https://example.com"],
                backend="requests",
                concurrency=5,
            )

            assert result == {"result": "sync"}
            MockClient.assert_called_once()
            call_kwargs = MockClient.call_args[1]
            assert call_kwargs["backend"] == "requests"
            assert call_kwargs["concurrency"] == 5
