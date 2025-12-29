import os
import asyncio
import time
import random
import re
from dataclasses import dataclass
from typing import Optional, List, Dict
from loguru import logger


@dataclass
class ProxyConfig:
    enabled: bool = False
    list: Optional[List[str]] = None
    webshare_url: Optional[str] = None
    free_proxies: bool = False
    retry_delay: float = 60.0
    validation_timeout: float = 5.0


class ProxyValidationError(Exception):
    pass


class ProxyManager:
    PROXY_PATTERNS = [
        r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$",
        r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}:[^:]+:[^:]+$",
        r"^http://[^:]+:[^@]+@[^:]+:\d+$",
        r"^https://[^:]+:[^@]+@[^:]+:\d+$",
    ]

    def __init__(self, config: ProxyConfig):
        self._config = config
        self._proxies: List[str] = []
        self._failed_proxies: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._load_proxies()

    @classmethod
    def _validate_ip_octets(cls, ip: str) -> bool:
        """Validate IP octets are in range 0-255"""
        octets = ip.split(".")
        if len(octets) != 4:
            return False
        try:
            return all(0 <= int(octet) <= 255 for octet in octets)
        except ValueError:
            return False

    def _load_proxies(self) -> None:
        proxies = []

        if self._config.list:
            proxies.extend(self._config.list)

        env_proxies = os.getenv("PROXIES", "")
        if env_proxies:
            proxies.extend(env_proxies.split(","))

        if self._config.webshare_url:
            webshare_proxies = self._load_webshare_proxies(self._config.webshare_url)
            proxies.extend(webshare_proxies)

        if self._config.free_proxies:
            free_proxies = self._fetch_free_proxies()
            proxies.extend(free_proxies)

        valid_count = 0
        filtered_count = 0
        self._proxies = []
        for proxy in proxies:
            if self.validate(proxy):
                self._proxies.append(proxy)
                valid_count += 1
            else:
                filtered_count += 1
                logger.debug(f"Filtered invalid proxy format: {proxy[:50]}...")

        if filtered_count > 0:
            logger.info(
                f"Loaded {valid_count} valid proxies, filtered {filtered_count} invalid proxies"
            )

    def _load_webshare_proxies(self, url: str) -> List[str]:
        import requests

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            proxies = []
            for line in response.text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(":")
                if len(parts) >= 4:
                    ip, port, user, pw = parts[:4]
                    proxy = f"http://{user}:{pw}@{ip}:{port}"
                    proxies.append(proxy)

            return proxies

        except Exception as e:
            raise ProxyValidationError(f"Failed to load webshare proxies: {e}") from e

    def _fetch_free_proxies(self) -> List[str]:
        return []

    @classmethod
    def validate(cls, proxy: str) -> bool:
        if not proxy or not isinstance(proxy, str):
            return False

        for pattern in cls.PROXY_PATTERNS:
            if re.match(pattern, proxy):
                if pattern in cls.PROXY_PATTERNS[:2]:
                    ip_part = proxy.split(":")[0]
                    if not cls._validate_ip_octets(ip_part):
                        return False
                return True

        return False

    async def get_next(self) -> Optional[str]:
        async with self._lock:
            now = time.time()

            self._failed_proxies = {p: t for p, t in self._failed_proxies.items() if t > now}

            available = [p for p in self._proxies if p not in self._failed_proxies]

            if not available:
                return None

            return random.choice(available)

    async def mark_failed(self, proxy: str) -> None:
        async with self._lock:
            if proxy in self._proxies:
                self._failed_proxies[proxy] = time.time() + self._config.retry_delay

    async def mark_success(self, proxy: str) -> None:
        async with self._lock:
            self._failed_proxies.pop(proxy, None)

    def count(self) -> int:
        return len(self._proxies)

    def count_available(self) -> int:
        now = time.time()
        return sum(
            1
            for p in self._proxies
            if p not in self._failed_proxies or self._failed_proxies[p] <= now
        )
