import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

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
            execute_shell_fn=self._execute_command,
            create_file_fn=self._create_file
        )
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

    def _create_file(self, path, content):
        """Mock function for creating files."""
        self.created_files.append((path, content))
        try:
            with open(path, 'w') as f:
                f.write(content)
            return 0
        except Exception:
            return -1

    def _setup_git_repos(self):
        """Set up real git repositories for testing."""
        # Set up origin repository
        self._execute_command(
            'git init --initial-branch=main', self.origin_dir
        )
        self._execute_command(
            "git config user.email 'test@example.com'", self.origin_dir
        )
        self._execute_command(
            "git config user.name 'Test User'", self.origin_dir
        )

        # Create a file and commit it
        with open(os.path.join(self.origin_dir, 'file1.txt'), 'w') as f:
            f.write('Original content')

        self._execute_command('git add file1.txt', self.origin_dir)
        self._execute_command(
            "git commit -m 'Initial commit'", self.origin_dir
        )

        # Clone the origin repository to local
        self._execute_command(
            f'git clone {self.origin_dir} {self.local_dir}'
        )
        self._execute_command(
            "git config user.email 'test@example.com'", self.local_dir
        )
        self._execute_command(
            "git config user.name 'Test User'", self.local_dir
        )

        # Create a feature branch in the local repository
        self._execute_command(
            'git checkout -b feature-branch', self.local_dir
        )

        # Modify a file and create a new file
        with open(os.path.join(self.local_dir, 'file1.txt'), 'w') as f:
            f.write('Modified content')

        with open(os.path.join(self.local_dir, 'file2.txt'), 'w') as f:
            f.write('New file content')

        # Add and commit file1.txt changes to create a baseline
        self._execute_command('git add file1.txt', self.local_dir)
        self._execute_command(
            "git commit -m 'Update file1.txt'", self.local_dir
        )

        # Add and commit file2.txt, then modify it
        self._execute_command('git add file2.txt', self.local_dir)
        self._execute_command(
            "git commit -m 'Add file2.txt'", self.local_dir
        )

        # Modify file2.txt and stage it
        with open(os.path.join(self.local_dir, 'file2.txt'), 'w') as f:
            f.write('Modified new file content')
        self._execute_command('git add file2.txt', self.local_dir)

        # Create a file that will be deleted
        with open(os.path.join(self.local_dir, 'file3.txt'), 'w') as f:
            f.write('File to be deleted')

        self._execute_command('git add file3.txt', self.local_dir)
        self._execute_command(
            "git commit -m 'Add file3.txt'", self.local_dir
        )
        self._execute_command('git rm file3.txt', self.local_dir)

        # Modify file1.txt again but don't stage it (unstaged change)
        with open(os.path.join(self.local_dir, 'file1.txt'), 'w') as f:
            f.write('Modified content again')

        # Push the feature branch to origin
        self._execute_command(
            'git push -u origin feature-branch', self.local_dir
        )

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
        
        # Call the method
        changes = self.git_handler.get_git_changes()
        
        # Verify the result
        self.assertEqual(changes, expected_changes)
        mock_git_changes_module.get_git_changes.assert_called_once_with(self.local_dir)

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
        
        # Call the method
        diff = self.git_handler.get_git_diff('file1.txt')
        
        # Verify the result
        self.assertEqual(diff, expected_diff)
        mock_git_diff_module.get_git_diff.assert_called_once_with('file1.txt')

    def test_create_python_script_file(self):
        """Test that _create_python_script_file creates a temporary Python script."""
        # Create a temporary script file for testing
        script_content = "print('Hello, World!')"
        script_path = os.path.join(self.test_dir, 'test_script.py')
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Mock the execute command to return a predictable temp file path
        temp_file_path = os.path.join(self.test_dir, 'temp_script.py')
        with patch.object(self.git_handler, 'execute') as mock_execute:
            mock_execute.side_effect = [
                CommandResult(temp_file_path, 0),  # mktemp result
                CommandResult('', 0)  # chmod result
            ]
            
            # Call the method
            result = self.git_handler._create_python_script_file(script_path)
            
            # Verify the result
            self.assertEqual(result, temp_file_path)
            self.assertEqual(len(self.created_files), 1)
            self.assertEqual(self.created_files[0][0], temp_file_path)
            self.assertEqual(self.created_files[0][1], script_content)

    @patch('openhands.runtime.utils.git_handler.git_changes')
    @patch('openhands.runtime.utils.git_handler.json')
    def test_get_git_changes_fallback(self, mock_json, mock_git_changes_module):
        """Test that get_git_changes falls back to creating a script file when needed."""
        # Mock the __file__ attribute
        type(mock_git_changes_module).__file__ = '/fake/path/git_changes.py'
        
        # Mock the execute command for the fallback path
        with patch.object(self.git_handler, 'execute') as mock_execute:
            # First call succeeds but returns invalid JSON
            mock_execute.return_value = CommandResult('invalid json', 0)
            
            # Mock json.loads to raise an exception and then return an empty list
            mock_json.loads.side_effect = [Exception("Invalid JSON"), []]
            
            # Mock _create_python_script_file
            with patch.object(self.git_handler, '_create_python_script_file') as mock_create_script:
                mock_create_script.return_value = '/tmp/git_changes.py'
                
                # Second call with the new script path returns valid JSON
                mock_execute.side_effect = [
                    CommandResult('invalid json', 0),  # First call
                    CommandResult('[]', 0)  # Second call with new script
                ]
                
                # Call the method - should use fallback
                changes = self.git_handler.get_git_changes()
                
                # Verify the script creation was attempted
                mock_create_script.assert_called_once()
                self.assertEqual(changes, [])

    @patch('openhands.runtime.utils.git_handler.git_diff')
    @patch('openhands.runtime.utils.git_handler.json')
    def test_get_git_diff_fallback(self, mock_json, mock_git_diff_module):
        """Test that get_git_diff falls back to creating a script file when needed."""
        # Mock the __file__ attribute
        type(mock_git_diff_module).__file__ = '/fake/path/git_diff.py'
        
        # Mock the execute command for the fallback path
        with patch.object(self.git_handler, 'execute') as mock_execute:
            # First call succeeds but returns invalid JSON
            mock_execute.return_value = CommandResult('invalid json', 0)
            
            # Mock json.loads to raise an exception and then return the expected diff
            expected_diff = {'original': 'content', 'modified': 'new content'}
            mock_json.loads.side_effect = [Exception("Invalid JSON"), expected_diff]
            
            # Mock _create_python_script_file
            with patch.object(self.git_handler, '_create_python_script_file') as mock_create_script:
                mock_create_script.return_value = '/tmp/git_diff.py'
                
                # Second call with the new script path returns valid JSON
                mock_execute.side_effect = [
                    CommandResult('invalid json', 0),  # First call
                    CommandResult('{"original": "content", "modified": "new content"}', 0)  # Second call with new script
                ]
                
                # Call the method - should use fallback
                diff = self.git_handler.get_git_diff('file1.txt')
                
                # Verify the script creation was attempted
                mock_create_script.assert_called_once()
                self.assertEqual(diff, expected_diff)
