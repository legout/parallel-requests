import pytest
from parallel_requests import parallel_requests, USER_AGENTS, PROXIES


class TestImports:
    def test_import_parallel_requests(self):
        """Test that parallel_requests can be imported."""
        assert parallel_requests is not None

    def test_import_user_agents(self):
        """Test that USER_AGENTS is a non-empty list."""
        assert isinstance(USER_AGENTS, list)
        assert len(USER_AGENTS) > 0

    def test_user_agents_are_strings(self):
        """Test that all user agents are strings."""
        assert all(isinstance(ua, str) for ua in USER_AGENTS)


class TestUserAgents:
    def test_user_agents_contain_common_browsers(self):
        """Test that user agents contain common browser identifiers."""
        user_agent_text = " ".join(USER_AGENTS).lower()
        assert "mozilla" in user_agent_text

    def test_user_agents_have_reasonable_length(self):
        """Test that user agents have reasonable length."""
        for ua in USER_AGENTS:
            assert len(ua) > 50, f"User agent too short: {ua}"
            assert len(ua) < 300, f"User agent too long: {ua}"
