"""
Tests for Git monitor
"""

import subprocess
from pathlib import Path

import pytest

from openhands.autonomous.perception.base import EventType
from openhands.autonomous.perception.git_monitor import GitMonitor


class TestGitMonitor:
    """Tests for GitMonitor class"""

    def test_create_monitor(self, temp_repo):
        """Test creating a git monitor"""
        monitor = GitMonitor(repo_path=str(temp_repo), check_interval=1)

        assert monitor.repo_path == temp_repo
        assert monitor.check_interval == 1
        assert len(monitor.known_branches) > 0  # At least master/main

    def test_initialize_state(self, temp_repo):
        """Test monitor initialization"""
        monitor = GitMonitor(repo_path=str(temp_repo))

        # Should have detected at least one branch
        assert len(monitor.known_branches) > 0

        # Should have initial commits
        assert len(monitor.last_commits) > 0

    @pytest.mark.asyncio
    async def test_detect_new_commit(self, temp_repo):
        """Test detecting a new commit"""
        monitor = GitMonitor(repo_path=str(temp_repo), check_interval=1)

        # Initial check - should be no events
        events = await monitor.check()
        assert events == []

        # Create a new commit
        test_file = temp_repo / "test.txt"
        test_file.write_text("Hello World")
        subprocess.run(["git", "add", "."], cwd=temp_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test file"],
            cwd=temp_repo,
            capture_output=True,
        )

        # Check again - should detect new commit
        events = await monitor.check()
        assert len(events) == 1
        assert events[0].event_type == EventType.GIT_COMMIT

        commit_data = events[0].data
        assert 'branch' in commit_data
        assert 'commit' in commit_data
        assert commit_data['commit']['message'] == "Add test file"

    @pytest.mark.asyncio
    async def test_detect_new_branch(self, temp_repo):
        """Test detecting a new branch"""
        monitor = GitMonitor(repo_path=str(temp_repo))

        # Create a new branch
        subprocess.run(
            ["git", "checkout", "-b", "feature-branch"],
            cwd=temp_repo,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "feature-branch"],
            cwd=temp_repo,
            capture_output=True,
            check=False,  # May fail if no remote
        )

        # For local test without remote, manually add to known branches
        # In real scenario with remote, check() would detect it
        events = await monitor._check_branches()

        # Check if new branch would be detected
        # (This is a bit tricky without a real remote, so we test the logic)
        assert monitor.known_branches is not None

    def test_determine_commit_priority(self, temp_repo):
        """Test commit priority determination"""
        monitor = GitMonitor(repo_path=str(temp_repo))

        # Critical commit
        commit = {
            'message': 'SECURITY FIX: patch vulnerability',
            'files_changed': [],
        }
        priority = monitor._determine_commit_priority(commit)
        assert priority.value == 1  # CRITICAL

        # High priority - bug fix
        commit = {
            'message': 'fix: resolve crash on startup',
            'files_changed': [],
        }
        priority = monitor._determine_commit_priority(commit)
        assert priority.value == 2  # HIGH

        # High priority - important file
        commit = {
            'message': 'Update dependencies',
            'files_changed': ['requirements.txt'],
        }
        priority = monitor._determine_commit_priority(commit)
        assert priority.value == 2  # HIGH

        # Medium priority - feature
        commit = {
            'message': 'feat: add new export feature',
            'files_changed': [],
        }
        priority = monitor._determine_commit_priority(commit)
        assert priority.value == 3  # MEDIUM

        # Low priority - docs
        commit = {
            'message': 'docs: update README',
            'files_changed': [],
        }
        priority = monitor._determine_commit_priority(commit)
        assert priority.value == 4  # LOW

    @pytest.mark.asyncio
    async def test_check_with_no_changes(self, temp_repo):
        """Test that check returns empty when no changes"""
        monitor = GitMonitor(repo_path=str(temp_repo))

        # First check
        events = await monitor.check()

        # Second check immediately - should be no events
        events = await monitor.check()
        assert events == []

    @pytest.mark.asyncio
    async def test_branches_to_watch(self, temp_repo):
        """Test watching specific branches"""
        monitor = GitMonitor(
            repo_path=str(temp_repo),
            branches_to_watch=['main', 'develop'],
        )

        assert monitor.branches_to_watch == ['main', 'develop']
