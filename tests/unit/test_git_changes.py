import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from openhands.runtime.utils.git_changes import git_status, get_git_changes


class TestGitChanges(unittest.TestCase):
    @patch('openhands.runtime.utils.git_changes.run')
    def test_git_status(self, mock_run):
        """Test that git_status correctly identifies changes in a git repository."""
        # Mock successful git status command with a modified file
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b'M file1.txt\n?? untracked.txt\n'
        mock_run.return_value = mock_result
        
        changes = git_status('/fake/repo')
        self.assertEqual(len(changes), 2)
        
        # Check the modified file
        self.assertEqual(changes[0]['status'], 'M')
        self.assertEqual(changes[0]['path'], 'file1.txt')
        
        # Check the untracked file (should be marked as 'A')
        self.assertEqual(changes[1]['status'], 'A')
        self.assertEqual(changes[1]['path'], 'untracked.txt')
        
        # Verify the command was called correctly
        mock_run.assert_called_once_with('git status --porcelain -uall', '/fake/repo')

    @patch('openhands.runtime.utils.git_changes.run')
    def test_git_status_with_error(self, mock_run):
        """Test that git_status handles errors gracefully."""
        # Mock a failed git command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        changes = git_status('/fake/repo')
        self.assertEqual(changes, [])

    @patch('openhands.runtime.utils.git_changes.glob.glob')
    @patch('openhands.runtime.utils.git_changes.git_status')
    def test_get_git_changes(self, mock_git_status, mock_glob):
        """Test that get_git_changes correctly identifies changes across multiple repositories."""
        # Mock finding two git repositories
        mock_glob.return_value = [
            './repo1/.git',
            './repo2/.git'
        ]
        
        # Mock git status results for main directory and subdirectories
        def mock_git_status_side_effect(cwd):
            if cwd == '/fake/workspace':
                return [{'status': 'M', 'path': 'workspace_file.txt'}]
            elif cwd == 'repo1':
                return [{'status': 'M', 'path': 'repo1_file.txt'}]
            elif cwd == 'repo2':
                return [{'status': 'A', 'path': 'untracked.txt'}]
            return []
        
        mock_git_status.side_effect = mock_git_status_side_effect
        
        # Call the function
        changes = get_git_changes('/fake/workspace')
        
        # Should find changes from all repositories
        self.assertEqual(len(changes), 3)
        
        # Verify the changes contain the expected items
        self.assertIn({'status': 'M', 'path': 'workspace_file.txt'}, changes)
        self.assertIn({'status': 'M', 'path': 'repo1/repo1_file.txt'}, changes)
        self.assertIn({'status': 'A', 'path': 'repo2/untracked.txt'}, changes)

    @patch('openhands.runtime.utils.git_changes.glob.glob')
    @patch('openhands.runtime.utils.git_changes.git_status')
    def test_get_git_changes_with_no_git_repos(self, mock_git_status, mock_glob):
        """Test that get_git_changes returns an empty list when no git repositories are found."""
        # Mock no git repositories found
        mock_glob.return_value = []
        
        # Mock empty git status for the main directory
        mock_git_status.return_value = []
        
        changes = get_git_changes('/fake/empty')
        self.assertEqual(changes, [])

    @patch('openhands.runtime.utils.git_changes.glob.glob')
    @patch('openhands.runtime.utils.git_changes.git_status')
    def test_get_git_changes_with_no_subdirs(self, mock_git_status, mock_glob):
        """Test that get_git_changes works correctly when there are no git subdirectories."""
        # Mock no git subdirectories found
        mock_glob.return_value = []
        
        # Mock git status for the main directory
        mock_git_status.return_value = [{'status': 'M', 'path': 'workspace_file.txt'}]
        
        changes = get_git_changes('/fake/workspace')
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['status'], 'M')
        self.assertEqual(changes[0]['path'], 'workspace_file.txt')


if __name__ == '__main__':
    unittest.main()