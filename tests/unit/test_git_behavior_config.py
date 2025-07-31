"""Tests for Git behavior configuration."""

from openhands.utils.prompt import GitBehaviorConfig


class TestGitBehaviorConfig:
    """Test Git behavior configuration."""

    def test_gui_behavior_config(self):
        """Test GUI interface behavior configuration."""
        config = GitBehaviorConfig(
            trigger_type='gui',
            auto_push=False,
            auto_pr=False,
        )

        assert config.trigger_type == 'gui'
        assert config.auto_push is False
        assert config.auto_pr is False

    def test_github_resolver_behavior_config(self):
        """Test GitHub resolver interface behavior configuration."""
        config = GitBehaviorConfig(
            trigger_type='github_resolver',
            auto_push=True,
            auto_pr=False,
        )

        assert config.trigger_type == 'github_resolver'
        assert config.auto_push is True
        assert config.auto_pr is False

    def test_slack_behavior_config(self):
        """Test Slack interface behavior configuration."""
        config = GitBehaviorConfig(
            trigger_type='slack',
            auto_push=False,
            auto_pr='ask_user',
        )

        assert config.trigger_type == 'slack'
        assert config.auto_push is False
        assert config.auto_pr == 'ask_user'

    def test_cli_behavior_config(self):
        """Test CLI interface behavior configuration."""
        config = GitBehaviorConfig(
            trigger_type='cli',
            auto_push=False,
            auto_pr=False,
        )

        assert config.trigger_type == 'cli'
        assert config.auto_push is False
        assert config.auto_pr is False
