import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from openhands.runtime.utils.git_handler import CommandResult, GitHandler


class TestGitHandler(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for our test repositories
        self.test_dir = tempfile.mkdtemp()
        self.origin_dir = os.path.join(self.test_dir, "origin")
        self.local_dir = os.path.join(self.test_dir, "local")
        
        # Create a mock execute function that will record commands and return predefined results
        self.executed_commands = []
        self.mock_execute = MagicMock()
        self.mock_execute.side_effect = self._mock_execute_side_effect
        
        # Initialize the GitHandler with our mock execute function
        self.git_handler = GitHandler(self.mock_execute)
        self.git_handler.set_cwd(self.local_dir)
        
        # Set up the git repositories
        self._setup_git_repos()

    def tearDown(self):
        # Clean up the temporary directories
        shutil.rmtree(self.test_dir)

    def _mock_execute_side_effect(self, cmd, cwd=None):
        """Side effect function for our mock execute function that simulates git commands."""
        self.executed_commands.append((cmd, cwd))
        
        # Handle different git commands
        if cmd == 'git rev-parse --is-inside-work-tree':
            return CommandResult('true', 0)
        
        elif cmd == 'git remote show origin | grep "HEAD branch"':
            return CommandResult('  HEAD branch: main', 0)
        
        elif cmd == 'git rev-parse --abbrev-ref HEAD':
            return CommandResult('feature-branch', 0)
        
        elif cmd.startswith('git rev-parse --verify'):
            # Simulate different refs existing or not
            ref = cmd.split(' ')[-1]
            if ref == 'origin/feature-branch':
                return CommandResult('', 0)  # This ref exists
            elif ref == '$(git merge-base HEAD "$(git rev-parse --abbrev-ref origin/main)")':
                return CommandResult('', 1)  # This ref doesn't exist
            elif ref == 'origin/main':
                return CommandResult('', 0)  # This ref exists
            elif ref.startswith('$(git rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904)'):
                return CommandResult('', 1)  # Empty tree ref doesn't exist
            else:
                return CommandResult('', 1)  # Default: ref doesn't exist
        
        elif cmd.startswith('git show'):
            # Simulate showing file content from a ref
            return CommandResult('content from ref', 0)
        
        elif cmd.startswith('cat '):
            # Simulate getting current file content
            return CommandResult('current content', 0)
        
        elif cmd.startswith('git diff'):
            # Simulate diff output
            return CommandResult('M\tfile1.txt\nA\tfile2.txt\nD\tfile3.txt', 0)
        
        elif cmd == 'git ls-files --others --exclude-standard':
            # Simulate untracked files
            return CommandResult('untracked1.txt\nuntracked2.txt', 0)
        
        # Default response for unhandled commands
        return CommandResult('', 0)

    def _setup_git_repos(self):
        """Set up the git repositories for testing."""
        # We don't actually need to create real git repos since we're mocking the git commands
        # This method is here for clarity and in case we want to use real repos in the future
        pass

    def test_is_git_repo(self):
        """Test that _is_git_repo returns True for a git repository."""
        self.assertTrue(self.git_handler._is_git_repo())
        self.mock_execute.assert_called_with('git rev-parse --is-inside-work-tree', self.local_dir)

    def test_get_default_branch(self):
        """Test that _get_default_branch returns the correct branch name."""
        branch = self.git_handler._get_default_branch()
        self.assertEqual(branch, 'main')
        self.mock_execute.assert_called_with('git remote show origin | grep "HEAD branch"', self.local_dir)

    def test_get_current_branch(self):
        """Test that _get_current_branch returns the correct branch name."""
        branch = self.git_handler._get_current_branch()
        self.assertEqual(branch, 'feature-branch')
        self.mock_execute.assert_called_with('git rev-parse --abbrev-ref HEAD', self.local_dir)

    def test_get_valid_ref(self):
        """Test that _get_valid_ref returns the highest priority valid ref."""
        ref = self.git_handler._get_valid_ref()
        self.assertIsNotNone(ref)
        
        # Check that the refs were checked in the correct order
        verify_commands = [cmd for cmd, _ in self.executed_commands if cmd.startswith('git rev-parse --verify')]
        
        # First should check origin/feature-branch (current branch)
        self.assertTrue(any('origin/feature-branch' in cmd for cmd in verify_commands))
        
        # Should have found a valid ref (origin/feature-branch)
        self.assertEqual(ref, 'origin/feature-branch')

    def test_get_ref_content(self):
        """Test that _get_ref_content returns the content from a valid ref."""
        content = self.git_handler._get_ref_content('file.txt')
        self.assertEqual(content, 'content from ref')
        
        # Should have called _get_valid_ref and then git show
        show_commands = [cmd for cmd, _ in self.executed_commands if cmd.startswith('git show')]
        self.assertTrue(any('file.txt' in cmd for cmd in show_commands))

    def test_get_current_file_content(self):
        """Test that _get_current_file_content returns the current content of a file."""
        content = self.git_handler._get_current_file_content('file.txt')
        self.assertEqual(content, 'current content')
        self.mock_execute.assert_called_with('cat file.txt', self.local_dir)

    def test_get_changed_files(self):
        """Test that _get_changed_files returns the list of changed files."""
        files = self.git_handler._get_changed_files()
        self.assertEqual(len(files), 3)
        self.assertEqual(files, ['M\tfile1.txt', 'A\tfile2.txt', 'D\tfile3.txt'])
        
        # Should have called _get_valid_ref and then git diff
        diff_commands = [cmd for cmd, _ in self.executed_commands if cmd.startswith('git diff')]
        self.assertTrue(diff_commands)

    def test_get_untracked_files(self):
        """Test that _get_untracked_files returns the list of untracked files."""
        files = self.git_handler._get_untracked_files()
        self.assertEqual(len(files), 2)
        self.assertEqual(files, [
            {'status': 'A', 'path': 'untracked1.txt'},
            {'status': 'A', 'path': 'untracked2.txt'}
        ])
        self.mock_execute.assert_called_with('git ls-files --others --exclude-standard', self.local_dir)

    def test_get_git_changes(self):
        """Test that get_git_changes returns the combined list of changed and untracked files."""
        changes = self.git_handler.get_git_changes()
        self.assertIsNotNone(changes)
        self.assertEqual(len(changes), 5)  # 3 changed + 2 untracked
        
        # Check that the changes include both changed and untracked files
        statuses = [change['status'] for change in changes]
        self.assertIn('M', statuses)  # Modified
        self.assertIn('A', statuses)  # Added
        self.assertIn('D', statuses)  # Deleted

    def test_get_git_diff(self):
        """Test that get_git_diff returns the original and modified content of a file."""
        diff = self.git_handler.get_git_diff('file.txt')
        self.assertEqual(diff, {
            'modified': 'current content',
            'original': 'content from ref'
        })
        
        # Should have called _get_current_file_content and _get_ref_content
        self.assertTrue(any('cat file.txt' in cmd for cmd, _ in self.executed_commands))
        self.assertTrue(any('git show' in cmd and 'file.txt' in cmd for cmd, _ in self.executed_commands))


if __name__ == '__main__':
    unittest.main()