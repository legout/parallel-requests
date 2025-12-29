import os
import random
from typing import Optional, List, Dict


class HeaderManager:
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    ]

    def __init__(
        self,
        random_user_agent: bool = True,
        user_agents: Optional[List[str]] = None,
        custom_user_agent: Optional[str] = None,
    ):
        self._enabled = random_user_agent
        self._custom_ua = custom_user_agent
        self._agents = self._load_user_agents(user_agents)

    def _load_user_agents(self, provided: Optional[List[str]]) -> List[str]:
        if provided:
            return provided

        env_agents = os.getenv("USER_AGENTS", "")
        if env_agents:
            return env_agents.split(",")

        remote_url = os.getenv("USER_AGENTS_URL", "")
        if remote_url:
            try:
                import requests

                response = requests.get(remote_url, timeout=10)
                response.raise_for_status()
                agents = [line.strip() for line in response.text.split("\n") if line.strip()]
                if agents:
                    return agents
            except Exception:
                pass

        return self.DEFAULT_USER_AGENTS.copy()

    def get_headers(
        self,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        headers = {}

        if self._enabled:
            if self._custom_ua:
                headers["user-agent"] = self._custom_ua
            else:
                headers["user-agent"] = random.choice(self._agents)

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def update_agents_from_remote(self, url: str) -> None:
        import requests

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            agents = [line.strip() for line in response.text.split("\n") if line.strip()]
            if agents:
                self._agents = agents
        except Exception as e:
            raise ValueError(f"Failed to update user agents: {e}") from e

    def set_custom_user_agent(self, user_agent: str) -> None:
        self._custom_ua = user_agent

    def get_user_agents(self) -> List[str]:
        return self._agents.copy()
