import pytest

from fastreq.backends.base import RequestConfig
from fastreq.backends.niquests import NiquestsBackend


@pytest.mark.asyncio
async def test_niquests_backend_name():
    backend = NiquestsBackend()
    assert backend.name == "niquests"


@pytest.mark.asyncio
async def test_niquests_backend_supports_http2():
    backend = NiquestsBackend()
    assert backend.supports_http2() is True


@pytest.mark.asyncio
async def test_niquests_backend_context_manager():
    async with NiquestsBackend() as backend:
        assert backend.name == "niquests"
        assert backend.supports_http2() is True


@pytest.mark.asyncio
async def test_niquests_backend_get_request():
    async with NiquestsBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/get", method="GET")
        response = await backend.request(config)

        assert response.status_code == 200
        assert "content-type" in response.headers
        assert isinstance(response.content, bytes)
        assert isinstance(response.text, str)
        assert response.url == "https://httpbin.org/get"
        assert isinstance(response.json_data, dict)


@pytest.mark.asyncio
async def test_niquests_backend_post_json():
    async with NiquestsBackend() as backend:
        data = {"key": "value", "number": 123}
        config = RequestConfig(url="https://httpbin.org/post", method="POST", json=data)
        response = await backend.request(config)

        assert response.status_code == 200
        assert response.json_data is not None
        assert response.json_data["json"] == data


@pytest.mark.asyncio
async def test_niquests_backend_post_data():
    async with NiquestsBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/post", method="POST", data="raw data")
        response = await backend.request(config)

        assert response.status_code == 200
        assert "raw data" in response.text


@pytest.mark.asyncio
async def test_niquests_backend_with_headers():
    async with NiquestsBackend() as backend:
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
async def test_niquests_backend_with_params():
    async with NiquestsBackend() as backend:
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
async def test_niquests_backend_streaming():
    async with NiquestsBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/bytes/1024", method="GET", stream=True)
        response = await backend.request(config)

        assert response.status_code == 200
        assert len(response.content) == 1024


@pytest.mark.asyncio
async def test_niquests_backend_timeout():
    async with NiquestsBackend() as backend:
        config = RequestConfig(url="https://httpbin.org/delay/1", method="GET", timeout=5.0)
        response = await backend.request(config)

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_niquests_backend_different_methods():
    async with NiquestsBackend() as backend:
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            config = RequestConfig(url=f"https://httpbin.org/{method.lower()}", method=method)
            response = await backend.request(config)

            assert response.status_code == 200, f"Failed for method {method}"


@pytest.mark.asyncio
async def test_niquests_backend_error_without_context_manager():
    backend = NiquestsBackend()
    config = RequestConfig(url="https://httpbin.org/get", method="GET")

    with pytest.raises(RuntimeError, match="Backend not initialized"):
        await backend.request(config)
