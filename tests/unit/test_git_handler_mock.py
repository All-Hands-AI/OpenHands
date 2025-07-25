import os
import unittest
from unittest.mock import patch, MagicMock

from openhands.runtime.utils.git_handler import GitHandler


class TestGitHandlerMock(unittest.TestCase):
    def setUp(self):
        # Mock functions for the GitHandler
        self.execute_command = MagicMock()
        self.create_file = MagicMock()
        
        # Initialize the GitHandler with mock functions
        self.git_handler = GitHandler(
            execute_shell_fn=self.execute_command,
            create_file_fn=self.create_file
        )
        self.git_handler.set_cwd('/fake/local')

    @patch('openhands.runtime.utils.git_handler.git_changes')
    def test_get_git_changes(self, mock_git_changes_module):
        """Test that get_git_changes delegates to the git_changes module."""
        # Mock the git_changes.get_git_changes function
        expected_changes = [
            {'status': 'M', 'path': 'file1.txt'},
            {'status': 'A', 'path': 'file2.txt'},
            {'status': 'D', 'path': 'file3.txt'},
            {'status': 'A', 'path': 'untracked.txt'}
        ]
        mock_git_changes_module.get_git_changes.return_value = expected_changes
        
        # Mock the __file__ attribute
        type(mock_git_changes_module).__file__ = '/fake/path/git_changes.py'
        
        # Mock the _create_python_script_file method to avoid file access
        with patch.object(self.git_handler, '_create_python_script_file') as mock_create_script:
            mock_create_script.return_value = '/tmp/git_changes.py'
            
            # Call the method
            changes = self.git_handler.get_git_changes()
            
            # Verify the result
            self.assertEqual(changes, expected_changes)
            mock_git_changes_module.get_git_changes.assert_called_once_with('/fake/local')

    @patch('openhands.runtime.utils.git_handler.git_diff')
    def test_get_git_diff(self, mock_git_diff_module):
        """Test that get_git_diff delegates to the git_diff module."""
        # Mock the git_diff.get_git_diff function
        expected_diff = {
            'original': 'Original content',
            'modified': 'Modified content again'
        }
        mock_git_diff_module.get_git_diff.return_value = expected_diff
        
        # Mock the __file__ attribute
        type(mock_git_diff_module).__file__ = '/fake/path/git_diff.py'
        
        # Mock the _create_python_script_file method to avoid file access
        with patch.object(self.git_handler, '_create_python_script_file') as mock_create_script:
            mock_create_script.return_value = '/tmp/git_diff.py'
            
            # Call the method
            diff = self.git_handler.get_git_diff('file1.txt')
            
            # Verify the result
            self.assertEqual(diff, expected_diff)
            mock_git_diff_module.get_git_diff.assert_called_once_with('file1.txt')


if __name__ == '__main__':
    unittest.main()