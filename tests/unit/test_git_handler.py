import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from openhands.runtime.utils import git_changes, git_diff, git_handler
from openhands.runtime.utils.git_handler import CommandResult, GitHandler


class TestGitHandler(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for our test repositories
        self.test_dir = tempfile.mkdtemp()
        self.origin_dir = os.path.join(self.test_dir, 'origin')
        self.local_dir = os.path.join(self.test_dir, 'local')

        # Create the directories
        os.makedirs(self.origin_dir, exist_ok=True)
        os.makedirs(self.local_dir, exist_ok=True)

        # Track executed commands for verification
        self.executed_commands = []
        self.created_files = []

        # Initialize the GitHandler with our mock functions
        self.git_handler = GitHandler(
            execute_shell_fn=self._execute_command, create_file_fn=self._create_file
        )
        self.git_handler.set_cwd(self.local_dir)

        self.git_handler.git_changes_cmd = f'python3 {git_changes.__file__}'
        self.git_handler.git_diff_cmd = f'python3 {git_diff.__file__} "{{file_path}}"'

        # Set up the git repositories
        self._setup_git_repos()

    def tearDown(self):
        # Clean up the temporary directories
        shutil.rmtree(self.test_dir)

    def _execute_command(self, cmd, cwd=None):
        """Execute a shell command and return the result."""
        self.executed_commands.append((cmd, cwd))
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False
            )
            time.sleep(0.5)
            return CommandResult(result.stdout, result.returncode)
        except Exception as e:
            return CommandResult(str(e), 1)

    def _create_file(self, path, content):
        """Mock function for creating files."""
        self.created_files.append((path, content))
        try:
            with open(path, 'w') as f:
                f.write(content)
            return 0
        except Exception:
            return -1

    def write_file(
        self,
        dir: str,
        name: str,
        additional_content: tuple[str, ...] = ('Line 1', 'Line 2', 'Line 3'),
    ):
        with open(os.path.join(dir, name), 'w') as f:
            f.write(name)
            for line in additional_content:
                f.write('\n')
                f.write(line)
        assert os.path.exists(os.path.join(dir, name))

    def _setup_git_repos(self):
        """Set up real git repositories for testing."""
        # Set up origin repository
        self._execute_command('git init --initial-branch=main', self.origin_dir)

        # Set up the initial state...
        self.write_file(self.origin_dir, 'unchanged.txt')
        self.write_file(self.origin_dir, 'committed_modified.txt')
        self.write_file(self.origin_dir, 'staged_modified.txt')
        self.write_file(self.origin_dir, 'unstaged_modified.txt')
        self.write_file(self.origin_dir, 'committed_delete.txt')
        self.write_file(self.origin_dir, 'staged_delete.txt')
        self.write_file(self.origin_dir, 'unstaged_delete.txt')
        self._execute_command(
            "git add . && git commit -m 'Initial Commit'", self.origin_dir
        )

        # Clone the origin repository to local
        self._execute_command(f'git clone {self.origin_dir} {self.local_dir}')
        time.sleep(1)

        expected_after_clone = [
            '.git',
            'committed_delete.txt',
            'committed_modified.txt',
            'staged_delete.txt',
            'staged_modified.txt',
            'unchanged.txt',
            'unstaged_delete.txt',
            'unstaged_modified.txt',
        ]
        cloned_content = sorted(os.listdir(self.local_dir))
        assert cloned_content == expected_after_clone

        self._execute_command('git checkout -b feature-branch', self.local_dir)

        # Setup committed changes...
        self.write_file(self.local_dir, 'committed_modified.txt', ('Line 4',))
        self.write_file(self.local_dir, 'committed_add.txt')
        os.remove(os.path.join(self.local_dir, 'committed_delete.txt'))
        self._execute_command(
            "git add . && git commit -m 'First batch of changes'", self.local_dir
        )

        # Setup staged changes...
        self.write_file(self.local_dir, 'staged_modified.txt', ('Line 4',))
        self.write_file(self.local_dir, 'staged_add.txt')
        os.remove(os.path.join(self.local_dir, 'staged_delete.txt'))
        self._execute_command('git add .', self.local_dir)

        # Setup unstaged changes...
        self.write_file(self.local_dir, 'unstaged_modified.txt', ('Line 4',))
        self.write_file(self.local_dir, 'unstaged_add.txt')
        os.remove(os.path.join(self.local_dir, 'unstaged_delete.txt'))

    def setup_nested(self):
        nested_1 = Path(self.local_dir, 'nested 1')
        nested_1.mkdir()
        nested_1 = str(nested_1)
        self._execute_command('git init --initial-branch=main', nested_1)
        self.write_file(nested_1, 'committed_add.txt')
        self._execute_command('git add .', nested_1)
        self._execute_command('git commit -m "Initial Commit"', nested_1)
        self.write_file(nested_1, 'staged_add.txt')

        nested_2 = Path(self.local_dir, 'nested_2')
        nested_2.mkdir()
        nested_2 = str(nested_2)
        self._execute_command('git init --initial-branch=main', nested_2)
        self.write_file(nested_2, 'committed_add.txt')
        self._execute_command('git add .', nested_2)
        self._execute_command('git commit -m "Initial Commit"', nested_2)
        self.write_file(nested_2, 'unstaged_add.txt')

    def test_get_git_changes(self):
        """
        Test with unpushed commits, staged commits, and unstaged commits
        """
        changes = self.git_handler.get_git_changes()

        expected_changes = [
            {'status': 'A', 'path': 'committed_add.txt'},
            {'status': 'D', 'path': 'committed_delete.txt'},
            {'status': 'M', 'path': 'committed_modified.txt'},
            {'status': 'A', 'path': 'staged_add.txt'},
            {'status': 'D', 'path': 'staged_delete.txt'},
            {'status': 'M', 'path': 'staged_modified.txt'},
            {'status': 'A', 'path': 'unstaged_add.txt'},
            {'status': 'D', 'path': 'unstaged_delete.txt'},
            {'status': 'M', 'path': 'unstaged_modified.txt'},
        ]

        assert changes == expected_changes

    def test_get_git_changes_after_push(self):
        """
        Test with staged commits, and unstaged commits
        """
        self._execute_command('git push -u origin feature-branch', self.local_dir)
        changes = self.git_handler.get_git_changes()

        expected_changes = [
            {'status': 'A', 'path': 'staged_add.txt'},
            {'status': 'D', 'path': 'staged_delete.txt'},
            {'status': 'M', 'path': 'staged_modified.txt'},
            {'status': 'A', 'path': 'unstaged_add.txt'},
            {'status': 'D', 'path': 'unstaged_delete.txt'},
            {'status': 'M', 'path': 'unstaged_modified.txt'},
        ]

        assert changes == expected_changes

    def test_get_git_changes_nested_repos(self):
        """
        Test with staged commits, and unstaged commits
        """
        self.setup_nested()

        changes = self.git_handler.get_git_changes()

        expected_changes = [
            {'status': 'A', 'path': 'committed_add.txt'},
            {'status': 'D', 'path': 'committed_delete.txt'},
            {'status': 'M', 'path': 'committed_modified.txt'},
            {'status': 'A', 'path': 'nested 1/staged_add.txt'},
            {'status': 'A', 'path': 'nested_2/unstaged_add.txt'},
            {'status': 'A', 'path': 'staged_add.txt'},
            {'status': 'D', 'path': 'staged_delete.txt'},
            {'status': 'M', 'path': 'staged_modified.txt'},
            {'status': 'A', 'path': 'unstaged_add.txt'},
            {'status': 'D', 'path': 'unstaged_delete.txt'},
            {'status': 'M', 'path': 'unstaged_modified.txt'},
        ]

        assert changes == expected_changes

    def test_get_git_diff_staged_modified(self):
        """Test on a staged modified"""
        diff = self.git_handler.get_git_diff('staged_modified.txt')
        expected_diff = {
            'original': 'staged_modified.txt\nLine 1\nLine 2\nLine 3',
            'modified': 'staged_modified.txt\nLine 4',
        }
        assert diff == expected_diff

    def test_get_git_diff_unchanged(self):
        """Test that get_git_diff delegates to the git_diff module."""
        diff = self.git_handler.get_git_diff('unchanged.txt')
        expected_diff = {
            'original': 'unchanged.txt\nLine 1\nLine 2\nLine 3',
            'modified': 'unchanged.txt\nLine 1\nLine 2\nLine 3',
        }
        assert diff == expected_diff

    def test_get_git_diff_unpushed(self):
        """Test that get_git_diff delegates to the git_diff module."""
        diff = self.git_handler.get_git_diff('committed_modified.txt')
        expected_diff = {
            'original': 'committed_modified.txt\nLine 1\nLine 2\nLine 3',
            'modified': 'committed_modified.txt\nLine 4',
        }
        assert diff == expected_diff

    def test_get_git_diff_unstaged_add(self):
        """Test that get_git_diff delegates to the git_diff module."""
        diff = self.git_handler.get_git_diff('unstaged_add.txt')
        expected_diff = {
            'original': '',
            'modified': 'unstaged_add.txt\nLine 1\nLine 2\nLine 3',
        }
        assert diff == expected_diff

    def test_get_git_changes_fallback(self):
        """Test that get_git_changes falls back to creating a script file when needed."""

        # Break the git changes command
        with patch(
            'openhands.runtime.utils.git_handler.GIT_CHANGES_CMD',
            'non-existant-command',
        ):
            self.git_handler.git_changes_cmd = git_handler.GIT_CHANGES_CMD

            changes = self.git_handler.get_git_changes()

            expected_changes = [
                {'status': 'A', 'path': 'committed_add.txt'},
                {'status': 'D', 'path': 'committed_delete.txt'},
                {'status': 'M', 'path': 'committed_modified.txt'},
                {'status': 'A', 'path': 'staged_add.txt'},
                {'status': 'D', 'path': 'staged_delete.txt'},
                {'status': 'M', 'path': 'staged_modified.txt'},
                {'status': 'A', 'path': 'unstaged_add.txt'},
                {'status': 'D', 'path': 'unstaged_delete.txt'},
                {'status': 'M', 'path': 'unstaged_modified.txt'},
            ]

            assert changes == expected_changes

    def test_get_git_diff_fallback(self):
        """Test that get_git_diff delegates to the git_diff module."""

        # Break the git diff command
        with patch(
            'openhands.runtime.utils.git_handler.GIT_DIFF_CMD', 'non-existant-command'
        ):
            self.git_handler.git_diff_cmd = git_handler.GIT_DIFF_CMD

            diff = self.git_handler.get_git_diff('unchanged.txt')
            expected_diff = {
                'original': 'unchanged.txt\nLine 1\nLine 2\nLine 3',
                'modified': 'unchanged.txt\nLine 1\nLine 2\nLine 3',
            }
            assert diff == expected_diff
