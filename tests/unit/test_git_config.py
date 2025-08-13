"""Tests for git configuration functionality."""

import os
from unittest.mock import patch

from openhands.core.config import OpenHandsConfig, load_from_env
from openhands.runtime.utils.command import get_action_execution_server_startup_command


class TestGitConfig:
    """Test git configuration functionality."""

    def test_default_git_config(self):
        """Test that default git configuration is set correctly."""
        config = OpenHandsConfig()
        assert config.git_user_name == "openhands"
        assert config.git_user_email == "openhands@all-hands.dev"

    def test_git_config_from_env_vars(self):
        """Test that git configuration can be set via environment variables."""
        with patch.dict(
            os.environ,
            {"GIT_USER_NAME": "testuser", "GIT_USER_EMAIL": "testuser@example.com"},
        ):
            config = OpenHandsConfig()
            load_from_env(config, os.environ)

            assert config.git_user_name == "testuser"
            assert config.git_user_email == "testuser@example.com"

    def test_git_config_in_command_generation(self):
        """Test that git configuration is properly passed to action execution server command."""
        config = OpenHandsConfig()
        config.git_user_name = "customuser"
        config.git_user_email = "customuser@example.com"

        cmd = get_action_execution_server_startup_command(
            server_port=8000,
            plugins=[],
            app_config=config,
            python_prefix=["python"],
            python_executable="python",
        )

        # Check that git config arguments are in the command
        assert "--git-user-name" in cmd
        assert "customuser" in cmd
        assert "--git-user-email" in cmd
        assert "customuser@example.com" in cmd

    def test_git_config_with_special_characters(self):
        """Test that git configuration handles special characters correctly."""
        config = OpenHandsConfig()
        config.git_user_name = "User With Spaces"
        config.git_user_email = "user+tag@example.com"

        cmd = get_action_execution_server_startup_command(
            server_port=8000,
            plugins=[],
            app_config=config,
            python_prefix=["python"],
            python_executable="python",
        )

        assert "User With Spaces" in cmd
        assert "user+tag@example.com" in cmd

    def test_git_config_empty_values(self):
        """Test behavior with empty git configuration values."""
        with patch.dict(os.environ, {"GIT_USER_NAME": "", "GIT_USER_EMAIL": ""}):
            config = OpenHandsConfig()
            load_from_env(config, os.environ)

            # Empty values should fall back to defaults
            assert config.git_user_name == "openhands"
            assert config.git_user_email == "openhands@all-hands.dev"
