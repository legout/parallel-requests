import os
import pytest
from unittest.mock import patch, MagicMock
from fastreq.utils.headers import HeaderManager


class TestHeaderManager:
    def test_init_default_user_agents(self):
        manager = HeaderManager()
        assert len(manager.get_user_agents()) >= 8

    def test_init_custom_user_agents(self):
        custom_agents = ["Agent1/1.0", "Agent2/2.0"]
        manager = HeaderManager(user_agents=custom_agents)
        assert manager.get_user_agents() == custom_agents

    def test_init_custom_user_agent_fixed(self):
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        assert manager._custom_ua == "MyApp/1.0"

    def test_init_disabled(self):
        manager = HeaderManager(random_user_agent=False)
        assert manager._enabled is False


class TestUserAgentRotation:
    def test_random_selection(self):
        manager = HeaderManager()
        headers1 = manager.get_headers()
        headers2 = manager.get_headers()
        assert "user-agent" in headers1
        assert "user-agent" in headers2

    def test_user_agent_present(self):
        manager = HeaderManager()
        headers = manager.get_headers()
        assert "user-agent" in headers

    def test_random_different_agents(self):
        manager = HeaderManager()
        agents = set()
        for _ in range(20):
            headers = manager.get_headers()
            agents.add(headers.get("user-agent"))
        assert len(agents) > 1


class TestCustomUserAgent:
    def test_custom_list_provided(self):
        custom_agents = ["Custom/1.0"]
        manager = HeaderManager(user_agents=custom_agents)
        headers = manager.get_headers()
        assert headers["user-agent"] == "Custom/1.0"

    def test_custom_user_agent_override(self):
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        headers = manager.get_headers()
        assert headers["user-agent"] == "MyApp/1.0"

    def test_custom_user_agent_fixed_no_rotation(self):
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        headers1 = manager.get_headers()
        headers2 = manager.get_headers()
        assert headers1["user-agent"] == headers2["user-agent"]

    def test_set_custom_user_agent(self):
        manager = HeaderManager()
        manager.set_custom_user_agent("NewApp/1.0")
        headers = manager.get_headers()
        assert headers["user-agent"] == "NewApp/1.0"


class TestEnvironmentVariable:
    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("USER_AGENTS", "Agent1,Agent2,Agent3")
        manager = HeaderManager()
        assert len(manager.get_user_agents()) == 3
        assert "Agent1" in manager.get_user_agents()

    def test_env_override_default(self, monkeypatch):
        monkeypatch.setenv("USER_AGENTS", "Agent1,Agent2,Agent3")
        manager = HeaderManager()
        agents = manager.get_user_agents()
        assert "Agent1" in agents
        assert "Mozilla" not in str(agents)

    @patch("requests.get")
    def test_load_from_remote_url_env(self, mock_get, monkeypatch):
        monkeypatch.setenv("USER_AGENTS_URL", "http://example.com/ua.txt")
        mock_response = MagicMock()
        mock_response.text = "RemoteAgent1\nRemoteAgent2"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = HeaderManager()
        assert len(manager.get_user_agents()) == 2
        assert "RemoteAgent1" in manager.get_user_agents()

    @patch("requests.get")
    def test_remote_url_failure_fallback(self, mock_get, monkeypatch):
        monkeypatch.setenv("USER_AGENTS_URL", "http://example.com/ua.txt")
        mock_get.side_effect = Exception("Network error")

        manager = HeaderManager()
        assert len(manager.get_user_agents()) >= 8
        assert "Mozilla" in str(manager.get_user_agents())


class TestHeaderMerging:
    def test_custom_headers_override_defaults(self):
        manager = HeaderManager()
        headers = manager.get_headers({"Authorization": "Bearer token"})
        assert headers["Authorization"] == "Bearer token"

    def test_custom_headers_preserve_user_agent(self):
        manager = HeaderManager()
        headers = manager.get_headers({"Authorization": "Bearer token"})
        assert "user-agent" in headers
        assert headers["Authorization"] == "Bearer token"

    def test_custom_user_agent_override_rotation(self):
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        headers = manager.get_headers()
        assert headers["user-agent"] == "MyApp/1.0"

    def test_no_custom_headers(self):
        manager = HeaderManager()
        headers = manager.get_headers()
        assert "user-agent" in headers
        assert len(headers) == 1

    def test_multiple_custom_headers(self):
        manager = HeaderManager()
        headers = manager.get_headers(
            {
                "Authorization": "Bearer token",
                "X-Custom": "value",
            }
        )
        assert headers["Authorization"] == "Bearer token"
        assert headers["X-Custom"] == "value"
        assert "user-agent" in headers


class TestRemoteUpdate:
    @patch("requests.get")
    def test_update_from_remote(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "NewAgent1\nNewAgent2\nNewAgent3"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = HeaderManager()
        manager.update_agents_from_remote("http://example.com/ua.txt")
        agents = manager.get_user_agents()
        assert len(agents) == 3
        assert "NewAgent1" in agents

    @patch("requests.get")
    def test_update_from_remote_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        manager = HeaderManager()
        with pytest.raises(ValueError, match="Failed to update user agents"):
            manager.update_agents_from_remote("http://example.com/ua.txt")

    @patch("requests.get")
    def test_update_from_remote_empty_lines(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "Agent1\n\nAgent2\n"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        manager = HeaderManager()
        manager.update_agents_from_remote("http://example.com/ua.txt")
        assert len(manager.get_user_agents()) == 2


class TestDisabledRotation:
    def test_disabled_no_user_agent(self):
        manager = HeaderManager(random_user_agent=False)
        headers = manager.get_headers()
        assert "user-agent" not in headers

    def test_disabled_with_custom_headers(self):
        manager = HeaderManager(random_user_agent=False)
        headers = manager.get_headers({"Authorization": "Bearer token"})
        assert "user-agent" not in headers
        assert headers["Authorization"] == "Bearer token"


class TestGetUserAgents:
    def test_get_user_agents_returns_copy(self):
        manager = HeaderManager()
        agents1 = manager.get_user_agents()
        agents2 = manager.get_user_agents()
        assert agents1 == agents2
        assert agents1 is not agents2
