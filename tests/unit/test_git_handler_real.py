import unittest
from unittest.mock import patch, MagicMock, mock_open

from openhands.runtime.utils.git_handler import CommandResult, GitHandler


class TestGitHandlerWithRealRepo(unittest.TestCase):
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
        """Test that get_git_changes returns the combined list of changed and untracked files."""
        # Mock the git_changes.get_git_changes function
        expected_changes = [
            {'status': 'M', 'path': 'file1.txt'},
            {'status': 'A', 'path': 'file2.txt'},
            {'status': 'A', 'path': 'untracked.txt'}
        ]
        mock_git_changes_module.get_git_changes.return_value = expected_changes
        
        # Mock the __file__ attribute
        type(mock_git_changes_module).__file__ = '/fake/path/git_changes.py'
        
        # Call the method
        changes = self.git_handler.get_git_changes()
        
        # Verify the result
        self.assertEqual(changes, expected_changes)
        mock_git_changes_module.get_git_changes.assert_called_once_with('/fake/local')

    @patch('openhands.runtime.utils.git_handler.git_diff')
    def test_get_git_diff(self, mock_git_diff_module):
        """Test that get_git_diff returns the original and modified content of a file."""
        # Mock the git_diff.get_git_diff function
        expected_diff = {
            'original': 'Modified content',
            'modified': 'Modified content again'
        }
        mock_git_diff_module.get_git_diff.return_value = expected_diff
        
        # Mock the __file__ attribute
        type(mock_git_diff_module).__file__ = '/fake/path/git_diff.py'
        
        # Call the method
        diff = self.git_handler.get_git_diff('file1.txt')
        
        # Verify the result
        self.assertEqual(diff, expected_diff)
        mock_git_diff_module.get_git_diff.assert_called_once_with('file1.txt')

    @patch('builtins.open', new_callable=mock_open, read_data='print("Hello, World!")')
    def test_create_python_script_file(self, mock_file):
        """Test that _create_python_script_file creates a temporary Python script."""
        # Mock the execute command to return a predictable temp file path
        self.execute_command.side_effect = [
            CommandResult('/tmp/temp_script.py', 0),  # mktemp result
            CommandResult('', 0)  # chmod result
        ]
        
        # Mock the create_file function
        self.create_file.return_value = 0
        
        # Call the method
        result = self.git_handler._create_python_script_file('/fake/script.py')
        
        # Verify the result
        self.assertEqual(result, '/tmp/temp_script.py')
        self.execute_command.assert_any_call('mktemp --suffix=.py', '/fake/local')
        self.execute_command.assert_any_call('chmod +x /tmp/temp_script.py', '/fake/local')
        self.create_file.assert_called_once()


if __name__ == '__main__':
    unittest.main()
