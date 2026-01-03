import pytest

from fastreq.backends.base import RequestConfig
from fastreq.backends.httpx import HttpxBackend


@pytest.mark.asyncio
async def test_httpx_backend_name():
    async with HttpxBackend() as backend:
        assert backend.name == "httpx"


@pytest.mark.asyncio
async def test_httpx_backend_supports_http2_enabled():
    backend = HttpxBackend(http2_enabled=True)
    assert backend.supports_http2() is False


@pytest.mark.asyncio
async def test_httpx_backend_supports_http2_disabled():
    backend = HttpxBackend(http2_enabled=False)
    assert backend.supports_http2() is False


@pytest.mark.asyncio
async def test_httpx_backend_context_manager():
    async with HttpxBackend() as backend:
        assert backend.name == "httpx"
        assert backend.supports_http2() is False


@pytest.mark.asyncio
async def test_httpx_backend_get_request():
    async with HttpxBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/get", method="GET")
        response = await backend.request(config)

        assert response.status_code == 200
        assert "content-type" in response.headers
        assert isinstance(response.content, bytes)
        assert isinstance(response.text, str)
        assert response.url == "https://httpbin.org/get"
        assert isinstance(response.json_data, dict)


@pytest.mark.asyncio
async def test_httpx_backend_post_json():
    async with HttpxBackend() as backend:
        data = {"key": "value", "number": 123}
        config = RequestConfig(url="https://httpbin.org/post", method="POST", json=data)
        response = await backend.request(config)

        assert response.status_code == 200
        assert response.json_data is not None
        assert response.json_data["json"] == data


@pytest.mark.asyncio
async def test_httpx_backend_post_data():
    async with HttpxBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/post", method="POST", data="raw data")
        response = await backend.request(config)

        assert response.status_code == 200
        assert "raw data" in response.text


@pytest.mark.asyncio
async def test_httpx_backend_with_headers():
    async with HttpxBackend() as backend:
        config = RequestConfig(
            url="https://httpbin.org/headers",
            method="GET",
            headers={"X-Custom-Header": "test-value"},
        )
        response = await backend.request(config)

        assert response.status_code == 200
        assert response.json_data is not None
        assert response.json_data["headers"]["X-Custom-Header"] == "test-value"


@pytest.mark.asyncio
async def test_httpx_backend_with_params():
    async with HttpxBackend() as backend:
        config = RequestConfig(
            url="https://httpbin.org/get",
            method="GET",
            params={"key": "value", "number": "42"},
        )
        response = await backend.request(config)

        assert response.status_code == 200
        assert response.json_data is not None
        assert response.json_data["args"]["key"] == "value"
        assert response.json_data["args"]["number"] == "42"


@pytest.mark.asyncio
async def test_httpx_backend_timeout():
    async with HttpxBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/delay/1", method="GET", timeout=5.0)
        response = await backend.request(config)

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_httpx_backend_different_methods():
    async with HttpxBackend() as backend:
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            config = RequestConfig(url=f"https://httpbin.org/{method.lower()}", method=method)
            response = await backend.request(config)

            assert response.status_code == 200, f"Failed for method {method}"


@pytest.mark.asyncio
async def test_httpx_backend_error_without_context_manager():
    backend = HttpxBackend()
    config = RequestConfig(url="https://httpbin.org/get", method="GET")

    with pytest.raises(RuntimeError, match="Backend not initialized"):
        await backend.request(config)


@pytest.mark.asyncio
async def test_httpx_backend_cookies():
    async with HttpxBackend() as backend:
        config = RequestConfig(
            url="https://httpbin.org/cookies",
            method="GET",
            cookies={"test_cookie": "test_value"},
        )
        response = await backend.request(config)

        assert response.status_code == 200
        assert response.json_data is not None
        assert response.json_data["cookies"]["test_cookie"] == "test_value"


@pytest.mark.asyncio
async def test_httpx_backend_follow_redirects():
    async with HttpxBackend() as backend:
        config = RequestConfig(
            url="https://httpbin.org/redirect-to?url=https://httpbin.org/get",
            method="GET",
            follow_redirects=True,
        )
        response = await backend.request(config)

        assert response.status_code == 200
        assert "get" in response.url


@pytest.mark.asyncio
async def test_httpx_backend_streaming():
    async with HttpxBackend() as backend:
        config = RequestConfig(
            url="https://httpbin.org/bytes/1024",
            method="GET",
            stream=True,
        )
        response = await backend.request(config)

        assert response.status_code == 200
        assert isinstance(response.content, bytes)
        assert len(response.content) == 1024
