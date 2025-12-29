import os
import tempfile
from pathlib import Path

import pytest

from parallel_requests.config import GlobalConfig


class TestGlobalConfigDefaults:
    def test_default_values(self) -> None:
        config = GlobalConfig()
        assert config.backend == "auto"
        assert config.default_concurrency == 20
        assert config.default_max_retries == 3
        assert config.rate_limit is None
        assert config.rate_limit_burst == 5
        assert config.http2_enabled is True
        assert config.random_user_agent is True
        assert config.random_proxy is False
        assert config.proxy_enabled is False
        assert config.free_proxies_enabled is False


class TestLoadFromEnv:
    def test_load_from_env_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PARALLEL_BACKEND", raising=False)
        monkeypatch.delenv("PARALLEL_CONCURRENCY", raising=False)
        monkeypatch.delenv("PARALLEL_MAX_RETRIES", raising=False)
        monkeypatch.delenv("PARALLEL_HTTP2", raising=False)
        monkeypatch.delenv("PARALLEL_RANDOM_USER_AGENT", raising=False)
        monkeypatch.delenv("PARALLEL_RANDOM_PROXY", raising=False)
        monkeypatch.delenv("PARALLEL_PROXY_ENABLED", raising=False)
        monkeypatch.delenv("PARALLEL_FREE_PROXIES", raising=False)

        config = GlobalConfig.load_from_env()

        assert config.backend == "auto"
        assert config.default_concurrency == 20
        assert config.default_max_retries == 3
        assert config.http2_enabled is True
        assert config.random_user_agent is True
        assert config.random_proxy is False
        assert config.proxy_enabled is False
        assert config.free_proxies_enabled is False

    def test_load_from_env_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PARALLEL_BACKEND", "niquests")
        monkeypatch.setenv("PARALLEL_CONCURRENCY", "50")
        monkeypatch.setenv("PARALLEL_MAX_RETRIES", "5")
        monkeypatch.setenv("PARALLEL_HTTP2", "false")
        monkeypatch.setenv("PARALLEL_RANDOM_USER_AGENT", "false")
        monkeypatch.setenv("PARALLEL_RANDOM_PROXY", "true")
        monkeypatch.setenv("PARALLEL_PROXY_ENABLED", "true")
        monkeypatch.setenv("PARALLEL_FREE_PROXIES", "true")

        config = GlobalConfig.load_from_env()

        assert config.backend == "niquests"
        assert config.default_concurrency == 50
        assert config.default_max_retries == 5
        assert config.http2_enabled is False
        assert config.random_user_agent is False
        assert config.random_proxy is True
        assert config.proxy_enabled is True
        assert config.free_proxies_enabled is True

    def test_load_from_env_rate_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PARALLEL_RATE_LIMIT", "10.5")
        monkeypatch.setenv("PARALLEL_RATE_LIMIT_BURST", "10")

        config = GlobalConfig.load_from_env()

        assert config.rate_limit == 10.5
        assert config.rate_limit_burst == 10


class TestToEnv:
    def test_to_env_contains_all_fields(self) -> None:
        config = GlobalConfig()
        env = config.to_env()

        assert "PARALLEL_BACKEND" in env
        assert "PARALLEL_CONCURRENCY" in env
        assert "PARALLEL_MAX_RETRIES" in env
        assert "PARALLEL_RATE_LIMIT" in env
        assert "PARALLEL_RATE_LIMIT_BURST" in env
        assert "PARALLEL_HTTP2" in env
        assert "PARALLEL_RANDOM_USER_AGENT" in env
        assert "PARALLEL_RANDOM_PROXY" in env
        assert "PARALLEL_PROXY_ENABLED" in env
        assert "PARALLEL_FREE_PROXIES" in env

    def test_to_env_custom_values(self) -> None:
        config = GlobalConfig(
            backend="niquests",
            default_concurrency=50,
            http2_enabled=False,
            random_user_agent=False,
        )
        env = config.to_env()

        assert env["PARALLEL_BACKEND"] == "niquests"
        assert env["PARALLEL_CONCURRENCY"] == "50"
        assert env["PARALLEL_HTTP2"] == "false"
        assert env["PARALLEL_RANDOM_USER_AGENT"] == "false"

    def test_to_env_bool_values_are_lowercase(self) -> None:
        config = GlobalConfig()
        env = config.to_env()

        assert env["PARALLEL_HTTP2"] == "true"
        assert env["PARALLEL_RANDOM_USER_AGENT"] == "true"
        assert env["PARALLEL_RANDOM_PROXY"] == "false"
        assert env["PARALLEL_PROXY_ENABLED"] == "false"
        assert env["PARALLEL_FREE_PROXIES"] == "false"

    def test_to_env_rate_limit_empty_when_none(self) -> None:
        config = GlobalConfig()
        env = config.to_env()

        assert env["PARALLEL_RATE_LIMIT"] == ""


class TestSaveToEnv:
    def test_save_to_env_creates_file(self) -> None:
        config = GlobalConfig(backend="niquests", default_concurrency=50)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            path = Path(f.name)

        try:
            config.save_to_env(path)
            content = path.read_text()
            assert "PARALLEL_BACKEND=niquests" in content
            assert "PARALLEL_CONCURRENCY=50" in content
        finally:
            path.unlink()

    def test_save_to_env_omits_empty_values(self) -> None:
        config = GlobalConfig(rate_limit=None)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            path = Path(f.name)

        try:
            config.save_to_env(path)
            content = path.read_text()
            lines = content.strip().split("\n")
            assert not any(line.startswith("PARALLEL_RATE_LIMIT=") for line in lines)
        finally:
            path.unlink()

    def test_save_to_env_with_path_string(self) -> None:
        config = GlobalConfig(backend="aiohttp")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.env")
            config.save_to_env(path)
            content = Path(path).read_text()
            assert "PARALLEL_BACKEND=aiohttp" in content
