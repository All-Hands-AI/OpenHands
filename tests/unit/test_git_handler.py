import os
import shutil
import subprocess
import tempfile
import unittest

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
        """Set up real git repositories for testing."""
        # Set up origin repository
        self._execute_command(
            'git --no-pager init --initial-branch=main', self.origin_dir
        )
        self._execute_command(
            "git --no-pager config user.email 'test@example.com'", self.origin_dir
        )
        self._execute_command(
            "git --no-pager config user.name 'Test User'", self.origin_dir
        )

        # Create a file and commit it
        with open(os.path.join(self.origin_dir, 'file1.txt'), 'w') as f:
            f.write('Original content')

        self._execute_command('git --no-pager add file1.txt', self.origin_dir)
        self._execute_command(
            "git --no-pager commit -m 'Initial commit'", self.origin_dir
        )

        # Clone the origin repository to local
        self._execute_command(
            f'git --no-pager clone {self.origin_dir} {self.local_dir}'
        )
        self._execute_command(
            "git --no-pager config user.email 'test@example.com'", self.local_dir
        )
        self._execute_command(
            "git --no-pager config user.name 'Test User'", self.local_dir
        )

        # Create a feature branch in the local repository
        self._execute_command(
            'git --no-pager checkout -b feature-branch', self.local_dir
        )

        # Modify a file and create a new file
        with open(os.path.join(self.local_dir, 'file1.txt'), 'w') as f:
            f.write('Modified content')

        with open(os.path.join(self.local_dir, 'file2.txt'), 'w') as f:
            f.write('New file content')

        # Add and commit file1.txt changes to create a baseline
        self._execute_command('git --no-pager add file1.txt', self.local_dir)
        self._execute_command(
            "git --no-pager commit -m 'Update file1.txt'", self.local_dir
        )

        # Add and commit file2.txt, then modify it
        self._execute_command('git --no-pager add file2.txt', self.local_dir)
        self._execute_command(
            "git --no-pager commit -m 'Add file2.txt'", self.local_dir
        )

        # Modify file2.txt and stage it
        with open(os.path.join(self.local_dir, 'file2.txt'), 'w') as f:
            f.write('Modified new file content')
        self._execute_command('git --no-pager add file2.txt', self.local_dir)

        # Create a file that will be deleted
        with open(os.path.join(self.local_dir, 'file3.txt'), 'w') as f:
            f.write('File to be deleted')

        self._execute_command('git --no-pager add file3.txt', self.local_dir)
        self._execute_command(
            "git --no-pager commit -m 'Add file3.txt'", self.local_dir
        )
        self._execute_command('git --no-pager rm file3.txt', self.local_dir)

        # Modify file1.txt again but don't stage it (unstaged change)
        with open(os.path.join(self.local_dir, 'file1.txt'), 'w') as f:
            f.write('Modified content again')

        # Push the feature branch to origin
        self._execute_command(
            'git --no-pager push -u origin feature-branch', self.local_dir
        )

    def test_is_git_repo(self):
        """Test that _is_git_repo returns True for a git repository."""
        self.assertTrue(self.git_handler._is_git_repo())

        # Verify the command was executed
        self.assertTrue(
            any(
                cmd == 'git --no-pager rev-parse --is-inside-work-tree'
                for cmd, _ in self.executed_commands
            )
        )

    def test_get_current_file_content(self):
        """Test that _get_current_file_content returns the current content of a file."""
        content = self.git_handler._get_current_file_content('file1.txt')
        self.assertEqual(content.strip(), 'Modified content again')

        # Verify the command was executed
        self.assertTrue(
            any(cmd == 'cat file1.txt' for cmd, _ in self.executed_commands)
        )

    def test_get_git_changes(self):
        """Test that get_git_changes returns the combined list of changed and untracked files."""
        # Create an untracked file
        with open(os.path.join(self.local_dir, 'untracked.txt'), 'w') as f:
            f.write('Untracked file content')

        # Create a new file and stage it
        with open(os.path.join(self.local_dir, 'new_file2.txt'), 'w') as f:
            f.write('New file 2 content')
        self._execute_command('git --no-pager add new_file2.txt', self.local_dir)

        changes = self.git_handler.get_git_changes()
        self.assertIsNotNone(changes)

        # Should include file1.txt (modified), file3.txt (deleted), new_file2.txt (added), and untracked.txt (untracked)
        paths = [change['path'] for change in changes]
        self.assertIn('file1.txt', paths)
        self.assertIn('file3.txt', paths)
        self.assertIn('new_file2.txt', paths)
        self.assertIn('untracked.txt', paths)

        # Check that the changes include both changed and untracked files
        statuses = [change['status'] for change in changes]
        self.assertIn('M', statuses)  # Modified
        self.assertIn('A', statuses)  # Added
        self.assertIn('D', statuses)  # Deleted

    def test_get_git_changes_multiple_repositories(self):
        """Test that get_git_changes can detect changes in multiple git repositories within a workspace."""
        # Create a workspace directory with multiple git repositories
        workspace_dir = os.path.join(self.test_dir, 'workspace')
        repo1_dir = os.path.join(workspace_dir, 'repo1')
        repo2_dir = os.path.join(workspace_dir, 'repo2')
        non_git_dir = os.path.join(workspace_dir, 'non_git')

        os.makedirs(workspace_dir, exist_ok=True)
        os.makedirs(repo1_dir, exist_ok=True)
        os.makedirs(repo2_dir, exist_ok=True)
        os.makedirs(non_git_dir, exist_ok=True)

        # Set up repo1
        self._execute_command('git --no-pager init', repo1_dir)
        self._execute_command(
            "git --no-pager config user.email 'test@example.com'", repo1_dir
        )
        self._execute_command("git --no-pager config user.name 'Test User'", repo1_dir)
        with open(os.path.join(repo1_dir, 'repo1_file.txt'), 'w') as f:
            f.write('repo1 content')
        self._execute_command('git --no-pager add repo1_file.txt', repo1_dir)
        self._execute_command("git --no-pager commit -m 'Initial commit'", repo1_dir)
        # Modify the file to create changes
        with open(os.path.join(repo1_dir, 'repo1_file.txt'), 'w') as f:
            f.write('repo1 modified content')

        # Set up repo2
        self._execute_command('git --no-pager init', repo2_dir)
        self._execute_command(
            "git --no-pager config user.email 'test@example.com'", repo2_dir
        )
        self._execute_command("git --no-pager config user.name 'Test User'", repo2_dir)
        with open(os.path.join(repo2_dir, 'repo2_file.txt'), 'w') as f:
            f.write('repo2 content')
        self._execute_command('git --no-pager add repo2_file.txt', repo2_dir)
        self._execute_command("git --no-pager commit -m 'Initial commit'", repo2_dir)
        # Add an untracked file
        with open(os.path.join(repo2_dir, 'untracked.txt'), 'w') as f:
            f.write('untracked content')

        # Add a file to the non-git directory (should be ignored)
        with open(os.path.join(non_git_dir, 'ignored_file.txt'), 'w') as f:
            f.write('ignored content')

        # Create a GitHandler for the workspace directory
        workspace_handler = GitHandler(self._execute_command)
        workspace_handler.set_cwd(workspace_dir)

        # Clear executed commands to start fresh
        self.executed_commands = []

        # Get changes from all repositories
        changes = workspace_handler.get_git_changes()
        self.assertIsNotNone(changes)

        # Should find changes from both repositories
        assert len(changes) == 2
        assert {'status': 'M', 'path': 'repo1/repo1_file.txt'} in changes
        assert {'status': 'A', 'path': 'repo2/untracked.txt'} in changes
