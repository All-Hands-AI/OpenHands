import os
import shutil
import subprocess
import tempfile
import unittest

from openhands.runtime.utils.git_handler import CommandResult, GitHandler


class TestGitHandlerWithRealRepo(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for our test repositories
        self.test_dir = tempfile.mkdtemp()
        self.origin_dir = os.path.join(self.test_dir, 'origin')
        self.local_dir = os.path.join(self.test_dir, 'local')

        # Create the directories
        os.makedirs(self.origin_dir, exist_ok=True)
        os.makedirs(self.local_dir, exist_ok=True)

        # Set up the git repositories
        self._setup_git_repos()

        # Initialize the GitHandler with a real execute function
        self.git_handler = GitHandler(self._execute_command)
        self.git_handler.set_cwd(self.local_dir)

    def tearDown(self):
        # Clean up the temporary directories
        shutil.rmtree(self.test_dir)

    def _execute_command(self, cmd, cwd=None):
        """Execute a shell command and return the result."""
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
        self._execute_command('git init --initial-branch=main', self.origin_dir)
        self._execute_command(
            "git config user.email 'test@example.com'", self.origin_dir
        )
        self._execute_command("git config user.name 'Test User'", self.origin_dir)

        # Create a file and commit it
        with open(os.path.join(self.origin_dir, 'file1.txt'), 'w') as f:
            f.write('Original content')

        self._execute_command('git add file1.txt', self.origin_dir)
        self._execute_command("git commit -m 'Initial commit'", self.origin_dir)

        # Clone the origin repository to local
        self._execute_command(f'git clone {self.origin_dir} {self.local_dir}')
        self._execute_command(
            "git config user.email 'test@example.com'", self.local_dir
        )
        self._execute_command("git config user.name 'Test User'", self.local_dir)

        # Create a feature branch in the local repository
        self._execute_command('git checkout -b feature-branch', self.local_dir)

        # Modify a file and create a new file
        with open(os.path.join(self.local_dir, 'file1.txt'), 'w') as f:
            f.write('Modified content')

        with open(os.path.join(self.local_dir, 'file2.txt'), 'w') as f:
            f.write('New file content')

        # Add the new file but don't commit anything yet
        self._execute_command('git add file2.txt', self.local_dir)

    def test_is_git_repo(self):
        """Test that _is_git_repo returns True for a git repository."""
        self.assertTrue(self.git_handler._is_git_repo())

    def test_get_default_branch(self):
        """Test that _get_default_branch returns the correct branch name."""
        branch = self.git_handler._get_default_branch()
        self.assertEqual(branch, 'main')

    def test_get_current_branch(self):
        """Test that _get_current_branch returns the correct branch name."""
        branch = self.git_handler._get_current_branch()
        self.assertEqual(branch, 'feature-branch')

    def test_get_valid_ref(self):
        """Test that _get_valid_ref returns a valid ref."""
        ref = self.git_handler._get_valid_ref()
        self.assertIsNotNone(ref)

        # Push the feature branch to origin to test the highest priority ref
        self._execute_command('git push -u origin feature-branch', self.local_dir)

        # Get the valid ref again, should be origin/feature-branch now
        ref = self.git_handler._get_valid_ref()
        self.assertIsNotNone(ref)

        # Verify the ref exists
        result = self._execute_command(f'git rev-parse --verify {ref}', self.local_dir)
        self.assertEqual(result.exit_code, 0)

    def test_get_ref_content(self):
        """Test that _get_ref_content returns the content from a valid ref."""
        # First commit the changes to make sure we have a valid ref
        self._execute_command('git add file1.txt', self.local_dir)
        self._execute_command("git commit -m 'Update file1.txt'", self.local_dir)

        # Get the content of file1.txt from the main branch
        content = self.git_handler._get_ref_content('file1.txt')
        self.assertEqual(content.strip(), 'Original content')

    def test_get_current_file_content(self):
        """Test that _get_current_file_content returns the current content of a file."""
        content = self.git_handler._get_current_file_content('file1.txt')
        self.assertEqual(content.strip(), 'Modified content')

    def test_get_changed_files(self):
        """Test that _get_changed_files returns the list of changed files."""
        files = self.git_handler._get_changed_files()
        self.assertTrue(files)

        # Should include file1.txt (modified) and file2.txt (added)
        file_paths = [line.split('\t')[-1] for line in files]
        self.assertIn('file1.txt', file_paths)
        self.assertIn('file2.txt', file_paths)

    def test_get_untracked_files(self):
        """Test that _get_untracked_files returns the list of untracked files."""
        # Create an untracked file
        with open(os.path.join(self.local_dir, 'untracked.txt'), 'w') as f:
            f.write('Untracked file content')

        files = self.git_handler._get_untracked_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['path'], 'untracked.txt')
        self.assertEqual(files[0]['status'], 'A')

    def test_get_git_changes(self):
        """Test that get_git_changes returns the combined list of changed and untracked files."""
        # Create an untracked file
        with open(os.path.join(self.local_dir, 'untracked.txt'), 'w') as f:
            f.write('Untracked file content')

        changes = self.git_handler.get_git_changes()
        self.assertIsNotNone(changes)

        # Should include file1.txt (modified), file2.txt (added), and untracked.txt (untracked)
        paths = [change['path'] for change in changes]
        self.assertIn('file1.txt', paths)
        self.assertIn('file2.txt', paths)
        self.assertIn('untracked.txt', paths)

    def test_get_git_diff(self):
        """Test that get_git_diff returns the original and modified content of a file."""
        diff = self.git_handler.get_git_diff('file1.txt')
        self.assertEqual(diff['modified'].strip(), 'Modified content')
        self.assertEqual(diff['original'].strip(), 'Original content')


if __name__ == '__main__':
    unittest.main()
