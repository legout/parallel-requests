import os
import random
from typing import Optional, List, Dict


class HeaderManager:
    """Manager for HTTP headers with user-agent rotation.

    Provides automatic user-agent rotation and custom header management.

    Example:
        >>> from parallel_requests.utils.headers import HeaderManager
        >>> manager = HeaderManager(random_user_agent=True)
        >>> headers = manager.get_headers({"Authorization": "Bearer token"})

    User agent sources (in order of priority):
        1. Custom user agent (if set via set_custom_user_agent)
        2. Provided user_agents list
        3. USER_AGENTS environment variable (comma-separated)
        4. USER_AGENTS_URL environment variable (fetch from URL)
        5. Default user agents
    """

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
        """Initialize HeaderManager.

        Args:
            random_user_agent: Enable random user-agent selection
            user_agents: Custom list of user agents (overrides defaults)
            custom_user_agent: Fixed user agent to use (overrides rotation)
        """
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
        """Get headers with optional user-agent.

        Args:
            custom_headers: Additional headers to include

        Returns:
            Dictionary of headers including user-agent if enabled
        """
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
        """Update user agent list from remote URL.

        Args:
            url: URL to fetch user agents from (one per line)

        Raises:
            ValueError: If fetch fails
        """
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
        """Set fixed custom user agent (disables rotation).

        Args:
            user_agent: User agent string to use
        """
        self._custom_ua = user_agent

    def get_user_agents(self) -> List[str]:
        """Get current list of user agents.

        Returns:
            Copy of user agent list
        """
        return self._agents.copy()
