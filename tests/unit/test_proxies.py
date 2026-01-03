import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastreq.utils.proxies import ProxyConfig, ProxyManager, ProxyValidationError


@pytest.fixture
def valid_config():
    return ProxyConfig(
        enabled=True,
        list=["http://user:pass@192.168.1.1:8080", "http://user:pass@192.168.1.2:8080"],
    )


@pytest.fixture
def empty_config():
    return ProxyConfig(enabled=True)


@pytest.fixture
def webshare_config():
    return ProxyConfig(
        enabled=True,
        webshare_url="http://example.com/proxies.txt",
    )


class TestProxyValidation:
    def test_validate_valid_ip_port(self):
        assert ProxyManager.validate("192.168.1.1:8080") is True

    def test_validate_valid_proxy_with_auth(self):
        assert ProxyManager.validate("192.168.1.1:8080:user:pass") is True

    def test_validate_valid_http_proxy_url(self):
        assert ProxyManager.validate("http://user:pass@192.168.1.1:8080") is True

    def test_validate_valid_https_proxy_url(self):
        assert ProxyManager.validate("https://user:pass@192.168.1.1:8080") is True

    def test_validate_invalid_malformed(self):
        assert ProxyManager.validate("malformed") is False

    def test_validate_empty_string(self):
        assert ProxyManager.validate("") is False

    def test_validate_none(self):
        assert ProxyManager.validate(None) is False

    def test_validate_non_string(self):
        assert ProxyManager.validate(123) is False

    def test_validate_invalid_ip_octets(self):
        assert ProxyManager.validate("999.999.999.999:8080") is False
        assert ProxyManager.validate("300.100.100.100:8080") is False


class TestProxyManager:
    def test_init_with_valid_proxies(self, valid_config):
        manager = ProxyManager(valid_config)
        assert manager.count() == 2

    def test_init_with_empty_list(self, empty_config):
        manager = ProxyManager(empty_config)
        assert manager.count() == 0

    def test_init_filters_invalid_proxies(self):
        config = ProxyConfig(
            enabled=True,
            list=["http://user:pass@192.168.1.1:8080", "invalid_proxy"],
        )
        manager = ProxyManager(config)
        assert manager.count() == 1

    @pytest.mark.asyncio
    async def test_get_next_returns_proxy(self, valid_config):
        manager = ProxyManager(valid_config)
        proxy = await manager.get_next()
        assert proxy in valid_config.list

    @pytest.mark.asyncio
    async def test_get_next_empty_list_returns_none(self, empty_config):
        manager = ProxyManager(empty_config)
        proxy = await manager.get_next()
        assert proxy is None

    @pytest.mark.asyncio
    async def test_get_next_random_selection(self, valid_config):
        manager = ProxyManager(valid_config)
        proxies = set()
        for _ in range(20):
            proxy = await manager.get_next()
            proxies.add(proxy)
        assert len(proxies) > 1

    @pytest.mark.asyncio
    async def test_mark_failed(self, valid_config):
        manager = ProxyManager(valid_config)
        proxy = await manager.get_next()
        await manager.mark_failed(proxy)
        assert manager.count_available() == 1

    @pytest.mark.asyncio
    async def test_failed_proxy_skipped(self, valid_config):
        manager = ProxyManager(valid_config)
        proxy = await manager.get_next()
        await manager.mark_failed(proxy)
        next_proxy = await manager.get_next()
        assert next_proxy != proxy

    @pytest.mark.asyncio
    async def test_failed_proxy_reenabled_after_delay(self):
        config = ProxyConfig(
            enabled=True,
            list=["http://user:pass@192.168.1.1:8080"],
            retry_delay=0.1,
        )
        manager = ProxyManager(config)
        proxy = await manager.get_next()
        await manager.mark_failed(proxy)
        assert manager.count_available() == 0
        await asyncio.sleep(0.2)
        assert manager.count_available() == 1

    @pytest.mark.asyncio
    async def test_mark_success_clears_failure(self, valid_config):
        manager = ProxyManager(valid_config)
        proxy = await manager.get_next()
        await manager.mark_failed(proxy)
        assert manager.count_available() == 1
        await manager.mark_success(proxy)
        assert manager.count_available() == 2

    def test_count(self, valid_config):
        manager = ProxyManager(valid_config)
        assert manager.count() == 2

    def test_count_available(self, valid_config):
        manager = ProxyManager(valid_config)
        assert manager.count_available() == 2


class TestWebshareIntegration:
    @patch("requests.get")
    def test_load_webshare_proxies_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "192.168.1.1:8080:user1:pass1\n192.168.1.2:8080:user2:pass2"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = ProxyManager(ProxyConfig(webshare_url="http://example.com"))
        assert manager.count() == 2

    @patch("requests.get")
    def test_load_webshare_proxies_format_conversion(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "192.168.1.1:8080:user:pass"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = ProxyManager(ProxyConfig(webshare_url="http://example.com"))
        assert manager._proxies[0] == "http://user:pass@192.168.1.1:8080"

    @patch("requests.get")
    def test_load_webshare_proxies_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(ProxyValidationError):
            ProxyManager(ProxyConfig(webshare_url="http://example.com"))

    @patch("requests.get")
    def test_load_webshare_proxies_empty_lines(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "192.168.1.1:8080:user:pass\n\n192.168.1.2:8080:user2:pass2\n"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = ProxyManager(ProxyConfig(webshare_url="http://example.com"))
        assert manager.count() == 2


class TestFreeProxies:
    def test_free_proxies_disabled_by_default(self):
        config = ProxyConfig(free_proxies=False)
        manager = ProxyManager(config)
        assert manager.count() == 0

    def test_free_proxies_opt_in(self):
        config = ProxyConfig(free_proxies=True)
        manager = ProxyManager(config)
        assert manager.count() == 0


class TestEnvironmentVariable:
    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("PROXIES", "http://user:pass@proxy1:8080,http://user:pass@proxy2:8080")
        manager = ProxyManager(ProxyConfig(enabled=True))
        assert manager.count() == 2
