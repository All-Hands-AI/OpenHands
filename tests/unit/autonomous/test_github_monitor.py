"""
Tests for GitHub Monitor
"""

import pytest

from openhands.autonomous.perception.base import EventType
from openhands.autonomous.perception.github_monitor import GitHubMonitor


class TestGitHubMonitor:
    """Tests for GitHubMonitor class"""

    def test_create_monitor(self):
        """Test creating a GitHub monitor"""
        monitor = GitHubMonitor(
            repo_owner="test-owner",
            repo_name="test-repo",
            check_interval=300,
            bot_username="openhands",
        )

        assert monitor.repo_owner == "test-owner"
        assert monitor.repo_name == "test-repo"
        assert monitor.bot_username == "openhands"

    def test_create_monitor_without_token(self, monkeypatch):
        """Test creating monitor without GitHub token"""
        monkeypatch.delenv('GITHUB_TOKEN', raising=False)

        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        assert monitor.github_token is None

    def test_create_monitor_with_token(self, monkeypatch):
        """Test creating monitor with GitHub token"""
        monkeypatch.setenv('GITHUB_TOKEN', 'test_token')

        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        assert monitor.github_token == 'test_token'

    @pytest.mark.asyncio
    async def test_check_without_token(self, monkeypatch):
        """Test check returns empty without token"""
        monkeypatch.delenv('GITHUB_TOKEN', raising=False)

        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        events = await monitor.check()

        assert events == []

    @pytest.mark.asyncio
    async def test_github_request_placeholder(self):
        """Test GitHub request placeholder"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )
        monitor.github_token = "test_token"

        result = await monitor._github_request('issues')

        # Placeholder returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_check_issues_no_data(self):
        """Test checking issues with no data"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )
        monitor.github_token = "test_token"

        events = await monitor._check_issues()

        # No data returns empty
        assert events == []

    @pytest.mark.asyncio
    async def test_check_pull_requests(self):
        """Test checking pull requests"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )
        monitor.github_token = "test_token"

        events = await monitor._check_pull_requests()

        # Placeholder implementation
        assert events == []

    @pytest.mark.asyncio
    async def test_check_mentions(self):
        """Test checking mentions"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )
        monitor.github_token = "test_token"

        events = await monitor._check_mentions()

        # Placeholder implementation
        assert events == []

    def test_determine_issue_priority_security(self):
        """Test issue priority for security issues"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        issue = {
            'title': 'Security vulnerability',
            'body': 'Found a security issue',
            'labels': [{'name': 'security'}],
        }

        priority = monitor._determine_issue_priority(issue)

        assert priority.value == 1  # CRITICAL

    def test_determine_issue_priority_bug(self):
        """Test issue priority for bugs"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        issue = {
            'title': 'Application crashes',
            'body': 'The app crashes on startup',
            'labels': [{'name': 'bug'}],
        }

        priority = monitor._determine_issue_priority(issue)

        assert priority.value == 2  # HIGH

    def test_determine_issue_priority_feature(self):
        """Test issue priority for features"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        issue = {
            'title': 'Add new feature',
            'body': 'Would be nice to have',
            'labels': [{'name': 'enhancement'}],
        }

        priority = monitor._determine_issue_priority(issue)

        assert priority.value == 3  # MEDIUM

    def test_determine_issue_priority_question(self):
        """Test issue priority for questions"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        issue = {
            'title': 'How do I...?',
            'body': 'I have a question',
            'labels': [{'name': 'question'}],
        }

        priority = monitor._determine_issue_priority(issue)

        assert priority.value == 4  # LOW

    def test_determine_issue_priority_by_content(self):
        """Test issue priority determined by content"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        issue = {
            'title': 'Application not working',
            'body': 'Everything is broken and crashes',
            'labels': [],
        }

        priority = monitor._determine_issue_priority(issue)

        # Should detect "broken", "crashes" in content
        assert priority.value == 2  # HIGH

    def test_determine_issue_priority_default(self):
        """Test default issue priority"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )

        issue = {
            'title': 'Some issue',
            'body': 'Some content',
            'labels': [],
        }

        priority = monitor._determine_issue_priority(issue)

        assert priority.value == 3  # MEDIUM (default)

    @pytest.mark.asyncio
    async def test_full_check_cycle(self):
        """Test complete check cycle"""
        monitor = GitHubMonitor(
            repo_owner="test",
            repo_name="repo",
        )
        monitor.github_token = "test_token"

        # Run full check
        events = await monitor.check()

        # Should update last check time
        assert monitor.last_check_time is not None
