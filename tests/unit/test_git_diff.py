import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from openhands.runtime.utils.git_diff import get_closest_git_repo, get_git_diff


class TestGitDiff(unittest.TestCase):
    @patch('pathlib.Path.is_dir')
    def test_get_closest_git_repo(self, mock_is_dir):
        """Test that get_closest_git_repo correctly finds the closest git repository."""
        # Mock the .git directory check to return True for a specific path
        mock_is_dir.side_effect = lambda: str(mock_is_dir._mock_self).endswith('repo/.git')
        
        # Test from root directory
        repo_path = get_closest_git_repo(Path('/fake/repo/file.txt'))
        self.assertEqual(repo_path, Path('/fake/repo'))
        
        # Test from subdirectory
        repo_path = get_closest_git_repo(Path('/fake/repo/subdir/file.txt'))
        self.assertEqual(repo_path, Path('/fake/repo'))
        
        # Test from nested subdirectory
        repo_path = get_closest_git_repo(Path('/fake/repo/subdir/nested/file.txt'))
        self.assertEqual(repo_path, Path('/fake/repo'))

    @patch('pathlib.Path.is_dir')
    def test_get_closest_git_repo_no_repo(self, mock_is_dir):
        """Test that get_closest_git_repo returns None when no git repository is found."""
        # Mock the .git directory check to always return False
        mock_is_dir.return_value = False
        
        repo_path = get_closest_git_repo(Path('/fake/non_git/file.txt'))
        self.assertIsNone(repo_path)

    @patch('openhands.runtime.utils.git_diff.get_closest_git_repo')
    @patch('openhands.runtime.utils.git_diff.run')
    @patch('openhands.runtime.utils.git_diff.open', new_callable=mock_open, read_data='modified content')
    @patch('openhands.runtime.utils.git_diff.os.getcwd')
    @patch('openhands.runtime.utils.git_diff.Path.resolve')
    @patch('openhands.runtime.utils.git_diff.Path.relative_to')
    def test_get_git_diff(self, mock_relative_to, mock_resolve, mock_getcwd, mock_open, mock_run, mock_get_closest_git_repo):
        """Test that get_git_diff correctly returns the original and modified content."""
        # Mock the current working directory
        mock_getcwd.return_value = '/fake/repo'
        
        # Mock the path resolution
        mock_resolve.return_value = Path('/fake/repo/file.txt')
        
        # Mock finding the git repository
        mock_get_closest_git_repo.return_value = Path('/fake/repo')
        
        # Mock the relative path
        mock_relative_to.return_value = Path('file.txt')
        
        # Mock the git commands
        mock_rev_result = MagicMock()
        mock_rev_result.stdout = b'main'
        mock_rev_result.returncode = 0
        
        mock_original_result = MagicMock()
        mock_original_result.stdout = b'original content'
        mock_original_result.returncode = 0
        
        mock_run.side_effect = [mock_rev_result, mock_original_result]
        
        # Get diff for the file
        diff = get_git_diff('file.txt')
        
        # Verify the result
        self.assertEqual(diff['modified'], 'modified content')
        self.assertEqual(diff['original'], 'original content')
        
        # Verify the git commands were called correctly
        mock_run.assert_any_call(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], '/fake/repo')
        mock_run.assert_any_call(['git', 'show', 'main:file.txt'], '/fake/repo')

    @patch('openhands.runtime.utils.git_diff.get_closest_git_repo')
    def test_get_git_diff_no_repo(self, mock_get_closest_git_repo):
        """Test that get_git_diff raises ValueError when no git repository is found."""
        # Mock not finding a git repository
        mock_get_closest_git_repo.return_value = None
        
        # Attempt to get diff for a file
        with self.assertRaises(ValueError) as context:
            get_git_diff('file.txt')
        
        self.assertEqual(str(context.exception), 'no_repo')

    @patch('openhands.runtime.utils.git_diff.get_closest_git_repo')
    @patch('openhands.runtime.utils.git_diff.run')
    @patch('openhands.runtime.utils.git_diff.open')
    @patch('openhands.runtime.utils.git_diff.os.getcwd')
    @patch('openhands.runtime.utils.git_diff.Path.resolve')
    @patch('openhands.runtime.utils.git_diff.Path.relative_to')
    def test_get_git_diff_file_not_found(self, mock_relative_to, mock_resolve, mock_getcwd, mock_open, mock_run, mock_get_closest_git_repo):
        """Test that get_git_diff handles the case where the file is not found."""
        # Mock the current working directory
        mock_getcwd.return_value = '/fake/repo'
        
        # Mock the path resolution
        mock_resolve.return_value = Path('/fake/repo/non_existent_file.txt')
        
        # Mock finding the git repository
        mock_get_closest_git_repo.return_value = Path('/fake/repo')
        
        # Mock the relative path
        mock_relative_to.return_value = Path('non_existent_file.txt')
        
        # Mock the git commands
        mock_rev_result = MagicMock()
        mock_rev_result.stdout = b'main'
        mock_rev_result.returncode = 0
        
        mock_original_result = MagicMock()
        mock_original_result.stdout = b'original content'
        mock_original_result.returncode = 0
        
        mock_run.side_effect = [mock_rev_result, mock_original_result]
        
        # Mock the file open to raise FileNotFoundError
        mock_open.side_effect = FileNotFoundError()
        
        # Get diff for a non-existent file
        diff = get_git_diff('non_existent_file.txt')
        
        # Verify the result
        self.assertEqual(diff['modified'], '')
        self.assertEqual(diff['original'], 'original content')


if __name__ == '__main__':
    unittest.main()