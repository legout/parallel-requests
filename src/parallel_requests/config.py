from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlobalConfig:
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
        p = Path(path) if isinstance(path, str) else path
        env_content = ""
        for key, value in self.to_env(prefix).items():
            if value:
                env_content += f"{key}={value}\n"
        p.write_text(env_content)
