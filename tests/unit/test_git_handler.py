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

    def test_get_default_branch(self):
        """Test that _get_default_branch returns the correct branch name."""
        branch = self.git_handler._get_default_branch()
        self.assertEqual(branch, 'main')

        # Verify the command was executed
        self.assertTrue(
            any(
                cmd == 'git --no-pager remote show origin | grep "HEAD branch"'
                for cmd, _ in self.executed_commands
            )
        )

    def test_get_current_branch(self):
        """Test that _get_current_branch returns the correct branch name."""
        branch = self.git_handler._get_current_branch()
        self.assertEqual(branch, 'feature-branch')
        print('executed commands:', self.executed_commands)

        # Verify the command was executed
        self.assertTrue(
            any(
                cmd == 'git --no-pager rev-parse --abbrev-ref HEAD'
                for cmd, _ in self.executed_commands
            )
        )

    def test_get_valid_ref_with_origin_current_branch(self):
        """Test that _get_valid_ref returns the current branch in origin when it exists."""
        # This test uses the setup from setUp where the current branch exists in origin
        ref = self.git_handler._get_valid_ref()
        self.assertIsNotNone(ref)

        # Check that the refs were checked in the correct order
        verify_commands = [
            cmd
            for cmd, _ in self.executed_commands
            if cmd.startswith('git --no-pager rev-parse --verify')
        ]

        # First should check origin/feature-branch (current branch)
        self.assertTrue(any('origin/feature-branch' in cmd for cmd in verify_commands))

        # Should have found a valid ref (origin/feature-branch)
        self.assertEqual(ref, 'origin/feature-branch')

        # Verify the ref exists
        result = self._execute_command(
            f'git --no-pager rev-parse --verify {ref}', self.local_dir
        )
        self.assertEqual(result.exit_code, 0)

    def test_get_valid_ref_without_origin_current_branch(self):
        """Test that _get_valid_ref falls back to default branch when current branch doesn't exist in origin."""
        # Create a new branch that doesn't exist in origin
        self._execute_command(
            'git --no-pager checkout -b new-local-branch', self.local_dir
        )

        # Clear the executed commands to start fresh
        self.executed_commands = []

        ref = self.git_handler._get_valid_ref()
        self.assertIsNotNone(ref)

        # Check that the refs were checked in the correct order
        verify_commands = [
            cmd
            for cmd, _ in self.executed_commands
            if cmd.startswith('git --no-pager rev-parse --verify')
        ]

        # Should have tried origin/new-local-branch first (which doesn't exist)
        self.assertTrue(
            any('origin/new-local-branch' in cmd for cmd in verify_commands)
        )

        # Should have found a valid ref (origin/main or merge-base)
        self.assertNotEqual(ref, 'origin/new-local-branch')
        self.assertTrue(ref == 'origin/main' or 'merge-base' in ref)

        # Verify the ref exists
        result = self._execute_command(
            f'git --no-pager rev-parse --verify {ref}', self.local_dir
        )
        self.assertEqual(result.exit_code, 0)

    def test_get_valid_ref_without_origin(self):
        """Test that _get_valid_ref falls back to empty tree ref when there's no origin."""
        # Create a new directory with a git repo but no origin
        no_origin_dir = os.path.join(self.test_dir, 'no-origin')
        os.makedirs(no_origin_dir, exist_ok=True)

        # Initialize git repo without origin
        self._execute_command('git --no-pager init', no_origin_dir)
        self._execute_command(
            "git --no-pager config user.email 'test@example.com'", no_origin_dir
        )
        self._execute_command(
            "git --no-pager config user.name 'Test User'", no_origin_dir
        )

        # Create a file and commit it
        with open(os.path.join(no_origin_dir, 'file1.txt'), 'w') as f:
            f.write('Content in repo without origin')
        self._execute_command('git --no-pager add file1.txt', no_origin_dir)
        self._execute_command(
            "git --no-pager commit -m 'Initial commit'", no_origin_dir
        )

        # Create a custom GitHandler with a modified _get_default_branch method for this test
        class TestGitHandler(GitHandler):
            def _get_default_branch(self) -> str:
                # Override to handle repos without origin
                try:
                    return super()._get_default_branch()
                except IndexError:
                    return 'main'  # Default fallback

        # Create a new GitHandler for this repo
        no_origin_handler = TestGitHandler(self._execute_command)
        no_origin_handler.set_cwd(no_origin_dir)

        # Clear the executed commands to start fresh
        self.executed_commands = []

        ref = no_origin_handler._get_valid_ref()

        # Verify that git commands were executed
        self.assertTrue(
            any(
                cmd.startswith('git --no-pager rev-parse --verify')
                for cmd, _ in self.executed_commands
            )
        )

        # Should have fallen back to the empty tree ref
        self.assertEqual(
            ref,
            '$(git --no-pager rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904)',
        )

        # Verify the ref exists (the empty tree ref always exists)
        result = self._execute_command(
            'git --no-pager rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904',
            no_origin_dir,
        )
        self.assertEqual(result.exit_code, 0)

    def test_get_ref_content(self):
        """Test that _get_ref_content returns the content from a valid ref."""
        content = self.git_handler._get_ref_content('file1.txt')
        self.assertEqual(content.strip(), 'Modified content')

        # Should have called _get_valid_ref and then git show
        show_commands = [
            cmd
            for cmd, _ in self.executed_commands
            if cmd.startswith('git --no-pager show')
        ]
        self.assertTrue(any('file1.txt' in cmd for cmd in show_commands))

    def test_get_current_file_content(self):
        """Test that _get_current_file_content returns the current content of a file."""
        content = self.git_handler._get_current_file_content('file1.txt')
        self.assertEqual(content.strip(), 'Modified content again')

        # Verify the command was executed
        self.assertTrue(
            any(cmd == 'cat file1.txt' for cmd, _ in self.executed_commands)
        )

    def test_get_changed_files(self):
        """Test that _get_changed_files returns the list of changed files."""
        # Let's create a new file to ensure it shows up in the diff
        with open(os.path.join(self.local_dir, 'new_file.txt'), 'w') as f:
            f.write('New file content')
        self._execute_command('git --no-pager add new_file.txt', self.local_dir)

        files = self.git_handler._get_changed_files()
        self.assertTrue(files)

        # Should include file1.txt (modified) and file3.txt (deleted)
        file_paths = [line.split('\t')[-1] for line in files if '\t' in line]
        self.assertIn('file1.txt', file_paths)
        self.assertIn('file3.txt', file_paths)
        # Also check for the new file
        self.assertIn('new_file.txt', file_paths)

        # Should have called _get_valid_ref and then git diff
        diff_commands = [
            cmd
            for cmd, _ in self.executed_commands
            if cmd.startswith('git --no-pager diff')
        ]
        self.assertTrue(diff_commands)

    def test_get_untracked_files(self):
        """Test that _get_untracked_files returns the list of untracked files."""
        # Create an untracked file
        with open(os.path.join(self.local_dir, 'untracked.txt'), 'w') as f:
            f.write('Untracked file content')

        files = self.git_handler._get_untracked_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['path'], 'untracked.txt')
        self.assertEqual(files[0]['status'], 'A')

        # Verify the command was executed
        self.assertTrue(
            any(
                cmd == 'git --no-pager ls-files --others --exclude-standard'
                for cmd, _ in self.executed_commands
            )
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

    def test_get_git_diff(self):
        """Test that get_git_diff returns the original and modified content of a file."""
        diff = self.git_handler.get_git_diff('file1.txt')
        self.assertEqual(diff['modified'].strip(), 'Modified content again')
        self.assertEqual(diff['original'].strip(), 'Modified content')

        # Should have called _get_current_file_content and _get_ref_content
        self.assertTrue(
            any('cat file1.txt' in cmd for cmd, _ in self.executed_commands)
        )
        self.assertTrue(
            any(
                'git --no-pager show' in cmd and 'file1.txt' in cmd
                for cmd, _ in self.executed_commands
            )
        )


if __name__ == '__main__':
    unittest.main()
