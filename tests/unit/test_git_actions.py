"""Tests for git commit and push actions."""

from unittest.mock import Mock

from openhands.events.action.git import GitCommitAction, GitPushAction
from openhands.events.observation.git import GitCommitObservation, GitPushObservation
from openhands.runtime.utils.git_handler import CommandResult, GitHandler


class TestGitActions:
    """Test git commit and push actions."""

    def test_git_commit_action_creation(self):
        """Test creating a GitCommitAction."""
        action = GitCommitAction(
            commit_message='Test commit message',
            files=['file1.py', 'file2.py'],
            add_all=False,
        )

        assert action.commit_message == 'Test commit message'
        assert action.files == ['file1.py', 'file2.py']
        assert action.add_all is False
        assert action.action == 'commit'

    def test_git_push_action_creation(self):
        """Test creating a GitPushAction."""
        action = GitPushAction(
            remote='origin',
            branch='main',
            force=False,
            set_upstream=True,
        )

        assert action.remote == 'origin'
        assert action.branch == 'main'
        assert action.force is False
        assert action.set_upstream is True
        assert action.action == 'push'

    def test_git_commit_observation_creation(self):
        """Test creating a GitCommitObservation."""
        obs = GitCommitObservation(
            content='Commit successful',
            commit_hash='abc123',
            files_committed=['file1.py', 'file2.py'],
        )

        assert obs.content == 'Commit successful'
        assert obs.commit_hash == 'abc123'
        assert obs.files_committed == ['file1.py', 'file2.py']
        assert obs.observation == 'commit'
        assert obs.success is True
        assert obs.error is False

    def test_git_push_observation_creation(self):
        """Test creating a GitPushObservation."""
        obs = GitPushObservation(
            content='Push successful',
            remote='origin',
            branch='main',
        )

        assert obs.content == 'Push successful'
        assert obs.remote == 'origin'
        assert obs.branch == 'main'
        assert obs.observation == 'push'
        assert obs.success is True
        assert obs.error is False

    def test_git_commit_observation_error_detection(self):
        """Test GitCommitObservation error detection."""
        obs = GitCommitObservation(
            content='Commit failed',
            commit_hash=None,
        )

        assert obs.success is False
        assert obs.error is True

    def test_git_push_observation_error_detection(self):
        """Test GitPushObservation error detection."""
        obs = GitPushObservation(
            content='error: failed to push some refs',
        )

        assert obs.success is False
        assert obs.error is True


class TestGitHandler:
    """Test GitHandler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_execute = Mock()
        self.mock_create_file = Mock()
        self.git_handler = GitHandler(
            execute_shell_fn=self.mock_execute,
            create_file_fn=self.mock_create_file,
        )
        self.git_handler.set_cwd('/test/workspace')

    def test_commit_changes_success(self):
        """Test successful git commit."""
        # Mock the command executions
        self.mock_execute.side_effect = [
            CommandResult(
                content='M  file1.py\nA  file2.py', exit_code=0
            ),  # git status --porcelain --cached
            CommandResult(
                content='file1.py\nfile2.py', exit_code=0
            ),  # git diff --cached --name-only
            CommandResult(
                content='[main abc123] Test commit', exit_code=0
            ),  # git commit
            CommandResult(content='abc123def456', exit_code=0),  # git rev-parse HEAD
        ]

        result = self.git_handler.commit_changes(
            message='Test commit',
            add_all=True,
        )

        assert result['success'] is True
        assert result['commit_hash'] == 'abc123def456'
        assert result['files_committed'] == ['file1.py', 'file2.py']

        # Verify the commands were called
        calls = self.mock_execute.call_args_list
        assert len(calls) == 4
        assert calls[0][0][0] == 'git add -A'
        assert calls[1][0][0] == 'git status --porcelain --cached'
        assert calls[2][0][0] == 'git diff --cached --name-only'
        assert calls[3][0][0] == 'git commit -m "Test commit"'

    def test_commit_changes_no_staged_changes(self):
        """Test git commit with no staged changes."""
        self.mock_execute.side_effect = [
            CommandResult(
                content='', exit_code=0
            ),  # git status --porcelain --cached (empty)
        ]

        result = self.git_handler.commit_changes(
            message='Test commit',
        )

        assert result['success'] is False
        assert 'No staged changes to commit' in result['error']

    def test_commit_changes_specific_files(self):
        """Test git commit with specific files."""
        self.mock_execute.side_effect = [
            CommandResult(content='', exit_code=0),  # git add file1.py
            CommandResult(content='', exit_code=0),  # git add file2.py
            CommandResult(
                content='M  file1.py\nA  file2.py', exit_code=0
            ),  # git status --porcelain --cached
            CommandResult(
                content='file1.py\nfile2.py', exit_code=0
            ),  # git diff --cached --name-only
            CommandResult(
                content='[main abc123] Test commit', exit_code=0
            ),  # git commit
            CommandResult(content='abc123def456', exit_code=0),  # git rev-parse HEAD
        ]

        result = self.git_handler.commit_changes(
            message='Test commit',
            files=['file1.py', 'file2.py'],
        )

        assert result['success'] is True
        assert result['files_committed'] == ['file1.py', 'file2.py']

    def test_push_changes_success(self):
        """Test successful git push."""
        self.mock_execute.side_effect = [
            CommandResult(content='main', exit_code=0),  # git branch --show-current
            CommandResult(
                content='To origin\n   abc123..def456  main -> main', exit_code=0
            ),  # git push
        ]

        result = self.git_handler.push_changes(
            remote='origin',
        )

        assert result['success'] is True
        assert result['remote'] == 'origin'
        assert result['branch'] == 'main'

        # Verify the commands were called
        calls = self.mock_execute.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == 'git branch --show-current'
        assert calls[1][0][0] == 'git push origin main'

    def test_push_changes_with_upstream(self):
        """Test git push with upstream setting."""
        self.mock_execute.side_effect = [
            CommandResult(
                content='feature-branch', exit_code=0
            ),  # git branch --show-current
            CommandResult(
                content="Branch 'feature-branch' set up to track remote branch",
                exit_code=0,
            ),  # git push -u
        ]

        result = self.git_handler.push_changes(
            remote='origin',
            set_upstream=True,
        )

        assert result['success'] is True

        # Verify the push command includes -u flag
        calls = self.mock_execute.call_args_list
        assert calls[1][0][0] == 'git push -u origin feature-branch'

    def test_push_changes_force(self):
        """Test git push with force flag."""
        self.mock_execute.side_effect = [
            CommandResult(content='main', exit_code=0),  # git branch --show-current
            CommandResult(
                content='+ abc123...def456 main -> main (forced update)', exit_code=0
            ),  # git push --force
        ]

        result = self.git_handler.push_changes(
            remote='origin',
            force=True,
        )

        assert result['success'] is True

        # Verify the push command includes --force flag
        calls = self.mock_execute.call_args_list
        assert calls[1][0][0] == 'git push --force origin main'

    def test_push_changes_error(self):
        """Test git push with error."""
        self.mock_execute.side_effect = [
            CommandResult(content='main', exit_code=0),  # git branch --show-current
            CommandResult(
                content='error: failed to push some refs', exit_code=1
            ),  # git push (error)
        ]

        result = self.git_handler.push_changes(
            remote='origin',
        )

        assert result['success'] is False
        assert 'failed to push some refs' in result['error']

    def test_push_changes_authentication_error(self):
        """Test git push with authentication error."""
        self.mock_execute.side_effect = [
            CommandResult(content='main', exit_code=0),  # git branch --show-current
            CommandResult(
                content='remote: Permission denied', exit_code=0
            ),  # git push (auth error)
        ]

        result = self.git_handler.push_changes(
            remote='origin',
        )

        assert result['success'] is False
        assert 'Permission denied' in result['error']
