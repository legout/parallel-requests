from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlobalConfig:
    """Global configuration for parallel requests.

    Can be loaded from environment variables or created programmatically.

    Example:
        >>> from fastreq.config import GlobalConfig
        >>> config = GlobalConfig(
        ...     backend="niquests",
        ...     default_concurrency=10,
        ... )
        >>> config.save_to_env(".env")

    Environment variables:
        PARALLEL_BACKEND: Backend to use ("auto", "niquests", "aiohttp", "requests")
        PARALLEL_CONCURRENCY: Default concurrency limit
        PARALLEL_MAX_RETRIES: Default max retries
        PARALLEL_RATE_LIMIT: Rate limit (requests per second)
        PARALLEL_RATE_LIMIT_BURST: Rate limit burst size
        PARALLEL_HTTP2: Enable HTTP/2 (true/false)
        PARALLEL_RANDOM_USER_AGENT: Rotate user agents (true/false)
        PARALLEL_RANDOM_PROXY: Enable proxy rotation (true/false)
        PARALLEL_PROXY_ENABLED: Enable proxies (true/false)
        PARALLEL_FREE_PROXIES: Enable free proxy fetching (true/false)

    Attributes:
        backend: Default backend selection
        default_concurrency: Default concurrency limit
        default_max_retries: Default maximum retry attempts
        rate_limit: Rate limit in requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2_enabled: Enable HTTP/2 support
        random_user_agent: Enable user agent rotation
        random_proxy: Enable proxy rotation
        proxy_enabled: Enable proxy usage
        free_proxies_enabled: Enable free proxy fetching
    """

    backend: str = "auto"
    default_concurrency: int = 20
    default_max_retries: int = 3
    rate_limit: float | None = None
    rate_limit_burst: int = 5
    http2_enabled: bool = True
    random_user_agent: bool = True
    random_proxy: bool = False
    proxy_enabled: bool = False
    free_proxies_enabled: bool = False

    @classmethod
    def load_from_env(cls, prefix: str = "PARALLEL_") -> "GlobalConfig":
        import os

        def get_bool(key: str, default: bool) -> bool:
            value = os.getenv(f"{prefix}{key}", str(default).lower())
            return value.lower() == "true"

        def get_int(key: str, default: int) -> int:
            value = os.getenv(f"{prefix}{key}")
            return int(value) if value is not None else default

        def get_float(key: str, default: float | None) -> float | None:
            value = os.getenv(f"{prefix}{key}")
            return float(value) if value is not None else default

        return cls(
            backend=os.getenv(f"{prefix}BACKEND", "auto"),
            default_concurrency=get_int("CONCURRENCY", 20),
            default_max_retries=get_int("MAX_RETRIES", 3),
            rate_limit=get_float("RATE_LIMIT", None),
            rate_limit_burst=get_int("RATE_LIMIT_BURST", 5),
            http2_enabled=get_bool("HTTP2", True),
            random_user_agent=get_bool("RANDOM_USER_AGENT", True),
            random_proxy=get_bool("RANDOM_PROXY", False),
            proxy_enabled=get_bool("PROXY_ENABLED", False),
            free_proxies_enabled=get_bool("FREE_PROXIES", False),
        )

    def to_env(self, prefix: str = "PARALLEL_") -> dict[str, str]:
        """Convert config to environment variable dictionary.

        Args:
            prefix: Prefix for environment variable names

        Returns:
            Dictionary of environment variable name to value
        """
        env: dict[str, str] = {
            f"{prefix}BACKEND": self.backend,
            f"{prefix}CONCURRENCY": str(self.default_concurrency),
            f"{prefix}MAX_RETRIES": str(self.default_max_retries),
            f"{prefix}RATE_LIMIT": str(self.rate_limit) if self.rate_limit else "",
            f"{prefix}RATE_LIMIT_BURST": str(self.rate_limit_burst),
            f"{prefix}HTTP2": str(self.http2_enabled).lower(),
            f"{prefix}RANDOM_USER_AGENT": str(self.random_user_agent).lower(),
            f"{prefix}RANDOM_PROXY": str(self.random_proxy).lower(),
            f"{prefix}PROXY_ENABLED": str(self.proxy_enabled).lower(),
            f"{prefix}FREE_PROXIES": str(self.free_proxies_enabled).lower(),
        }
        return env

    def save_to_env(self, path: Path | str, prefix: str = "PARALLEL_") -> None:
        """Save configuration to an environment file.

        Args:
            path: Path to save the .env file
            prefix: Prefix for environment variable names

        Example:
            >>> config = GlobalConfig(backend="niquests")
            >>> config.save_to_env(".env")
        """
        p = Path(path) if isinstance(path, str) else path
        env_content = ""
        for key, value in self.to_env(prefix).items():
            if value:
                env_content += f"{key}={value}\n"
        p.write_text(env_content)
