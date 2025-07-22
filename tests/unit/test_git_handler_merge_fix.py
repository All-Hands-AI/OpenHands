import os
import shutil
import subprocess
import tempfile
import unittest

from openhands.runtime.utils.git_handler import CommandResult, GitHandler


class TestGitHandlerMergeFix(unittest.TestCase):
    """Test the fix for git changes showing merged files as user changes."""

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

        # Initialize the GitHandler with our real execute function
        self.git_handler = GitHandler(self._execute_command)
        self.git_handler.set_cwd(self.local_dir)

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
            return CommandResult(result.stdout, result.returncode)
        except Exception as e:
            return CommandResult(str(e), 1)

    def _setup_git_repos(self):
        """Set up git repositories for testing the merge scenario."""
        # Set up origin repository
        self._execute_command('git init --initial-branch=main', self.origin_dir)
        self._execute_command(
            "git config user.email 'test@example.com'", self.origin_dir
        )
        self._execute_command("git config user.name 'Test User'", self.origin_dir)

        # Create initial file and commit
        with open(os.path.join(self.origin_dir, 'file1.txt'), 'w') as f:
            f.write('Initial content\n')

        self._execute_command('git add file1.txt', self.origin_dir)
        self._execute_command("git commit -m 'Initial commit'", self.origin_dir)

        # Clone to local
        self._execute_command(f'git clone {self.origin_dir} {self.local_dir}')
        self._execute_command(
            "git config user.email 'test@example.com'", self.local_dir
        )
        self._execute_command("git config user.name 'Test User'", self.local_dir)

        # Create a feature branch
        self._execute_command('git checkout -b feature-branch', self.local_dir)

        # Make some changes on feature branch
        with open(os.path.join(self.local_dir, 'feature_file.txt'), 'w') as f:
            f.write('Feature content\n')

        self._execute_command('git add feature_file.txt', self.local_dir)
        self._execute_command("git commit -m 'Add feature file'", self.local_dir)

        # Push feature branch to origin
        self._execute_command('git push -u origin feature-branch', self.local_dir)

        # Now simulate main branch getting ahead
        # Switch to main in origin and add more commits
        self._execute_command('git checkout main', self.origin_dir)

        with open(os.path.join(self.origin_dir, 'main_file1.txt'), 'w') as f:
            f.write('Main content 1\n')
        self._execute_command('git add main_file1.txt', self.origin_dir)
        self._execute_command("git commit -m 'Add main file 1'", self.origin_dir)

        with open(os.path.join(self.origin_dir, 'main_file2.txt'), 'w') as f:
            f.write('Main content 2\n')
        self._execute_command('git add main_file2.txt', self.origin_dir)
        self._execute_command("git commit -m 'Add main file 2'", self.origin_dir)

    def test_git_changes_before_merge(self):
        """Test that git changes shows no changes before merge."""
        changes = self.git_handler.get_git_changes()
        self.assertEqual(changes, [])

    def test_git_changes_after_merge_shows_only_user_changes(self):
        """Test that git changes after merge shows only user changes, not merged files."""
        # First, fetch latest changes from main
        self._execute_command('git fetch origin', self.local_dir)

        # Merge main into feature branch
        self._execute_command('git merge origin/main', self.local_dir)

        # Clear executed commands to start fresh for the git handler calls
        self.executed_commands = []

        # Get git changes after merge
        changes = self.git_handler.get_git_changes()

        # Should only show the feature file, not the merged files
        self.assertIsNotNone(changes)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['path'], 'feature_file.txt')
        self.assertEqual(changes[0]['status'], 'A')

        # Verify that the merged files are not shown as changes
        paths = [change['path'] for change in changes]
        self.assertNotIn('main_file1.txt', paths)
        self.assertNotIn('main_file2.txt', paths)

    def test_divergence_detection_after_merge(self):
        """Test that divergence detection correctly identifies merge scenarios."""
        # Before merge, should not detect divergence
        has_diverged_before = (
            self.git_handler._has_diverged_from_remote_tracking_branch(
                'feature-branch', 'main'
            )
        )
        self.assertFalse(has_diverged_before)

        # Fetch and merge
        self._execute_command('git fetch origin', self.local_dir)
        self._execute_command('git merge origin/main', self.local_dir)

        # After merge, should detect divergence
        has_diverged_after = self.git_handler._has_diverged_from_remote_tracking_branch(
            'feature-branch', 'main'
        )
        self.assertTrue(has_diverged_after)

    def test_valid_ref_selection_after_merge(self):
        """Test that _get_valid_ref selects merge-base after detecting divergence."""
        # Fetch and merge
        self._execute_command('git fetch origin', self.local_dir)
        self._execute_command('git merge origin/main', self.local_dir)

        # Clear executed commands to start fresh
        self.executed_commands = []

        # Get valid ref
        valid_ref = self.git_handler._get_valid_ref()

        # Should use merge-base instead of remote tracking branch
        self.assertIsNotNone(valid_ref)
        self.assertIn('merge-base', valid_ref)
        self.assertNotEqual(valid_ref, 'origin/feature-branch')


if __name__ == '__main__':
    unittest.main()
