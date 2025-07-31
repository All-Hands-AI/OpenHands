import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from openhands.core.logger import openhands_logger as logger
from openhands.runtime.utils import git_changes, git_diff

GIT_CHANGES_CMD = 'python3 /openhands/code/openhands/runtime/utils/git_changes.py'
GIT_DIFF_CMD = (
    'python3 /openhands/code/openhands/runtime/utils/git_diff.py "{file_path}"'
)


@dataclass
class CommandResult:
    """
    Represents the result of a shell command execution.

    Attributes:
        content (str): The output content of the command.
        exit_code (int): The exit code of the command execution.
    """

    content: str
    exit_code: int


class GitHandler:
    """
    A handler for executing Git-related operations via shell commands.
    """

    def __init__(
        self,
        execute_shell_fn: Callable[[str, str | None], CommandResult],
        create_file_fn: Callable[[str, str], int],
    ):
        self.execute = execute_shell_fn
        self.create_file_fn = create_file_fn
        self.cwd: str | None = None
        self.git_changes_cmd = GIT_CHANGES_CMD
        self.git_diff_cmd = GIT_DIFF_CMD

    def set_cwd(self, cwd: str) -> None:
        """
        Sets the current working directory for Git operations.

        Args:
            cwd (str): The directory path.
        """
        self.cwd = cwd

    def _create_python_script_file(self, file: str):
        result = self.execute('mktemp -d', self.cwd)
        script_file = Path(result.content.strip(), Path(file).name)
        with open(file, 'r') as f:
            self.create_file_fn(str(script_file), f.read())
            result = self.execute(f'chmod +x "{script_file}"', self.cwd)
        return script_file

    def get_git_changes(self) -> list[dict[str, str]] | None:
        """
        Retrieves the list of changed files in Git repositories.
        Examines each direct subdirectory of the workspace directory looking for git repositories
        and returns the changes for each of these directories.
        Optimized to use a single git command per repository for maximum performance.

        Returns:
            list[dict[str, str]] | None: A list of dictionaries containing file paths and statuses. None if no git repositories found.
        """
        # If cwd is not set, return None
        if not self.cwd:
            return None

        result = self.execute(self.git_changes_cmd, self.cwd)
        if result.exit_code == 0:
            try:
                changes = json.loads(result.content)
                return changes
            except Exception:
                logger.exception(
                    'GitHandler:get_git_changes:error',
                    extra={'content': result.content},
                )
                return None

        if self.git_changes_cmd != GIT_CHANGES_CMD:
            # We have already tried to add a script to the workspace - it did not work
            return None

        # We try to add a script for getting git changes to the runtime - legacy runtimes may be missing the script
        logger.info(
            'GitHandler:get_git_changes: adding git_changes script to runtime...'
        )
        script_file = self._create_python_script_file(git_changes.__file__)
        self.git_changes_cmd = f'python3 {script_file}'

        # Try again with the new changes cmd
        return self.get_git_changes()

    def get_git_diff(self, file_path: str) -> dict[str, str]:
        """
        Retrieves the original and modified content of a file in the repository.

        Args:
            file_path (str): Path to the file.

        Returns:
            dict[str, str]: A dictionary containing the original and modified content.
        """
        # If cwd is not set, return None
        if not self.cwd:
            raise ValueError('no_dir_in_git_diff')

        result = self.execute(self.git_diff_cmd.format(file_path=file_path), self.cwd)
        if result.exit_code == 0:
            diff = json.loads(result.content)
            return diff

        if self.git_diff_cmd != GIT_DIFF_CMD:
            # We have already tried to add a script to the workspace - it did not work
            raise ValueError('error_in_git_diff')

        # We try to add a script for getting git changes to the runtime - legacy runtimes may be missing the script
        logger.info('GitHandler:get_git_diff: adding git_diff script to runtime...')
        script_file = self._create_python_script_file(git_diff.__file__)
        self.git_diff_cmd = f'python3 {script_file} "{{file_path}}"'

        # Try again with the new changes cmd
        return self.get_git_diff(file_path)

    def commit_changes(
        self,
        message: str,
        files: list[str] | None = None,
        add_all: bool = False,
    ) -> dict[str, str | list[str] | bool | None]:
        """
        Commits changes to the git repository.

        Args:
            message (str): Commit message
            files (list[str] | None): Specific files to commit, if None commits all staged files
            add_all (bool): If True, stages all changes before committing (git add -A)

        Returns:
            dict: A dictionary containing commit information including hash and files committed
        """
        if not self.cwd:
            raise ValueError('no_dir_in_git_commit')

        try:
            # Stage files if needed
            if add_all:
                stage_result = self.execute('git add -A', self.cwd)
                if stage_result.exit_code != 0:
                    return {
                        'success': False,
                        'error': f'Failed to stage files: {stage_result.content}',
                        'commit_hash': None,
                        'files_committed': None,
                    }
            elif files:
                # Stage specific files
                for file in files:
                    stage_result = self.execute(f'git add "{file}"', self.cwd)
                    if stage_result.exit_code != 0:
                        return {
                            'success': False,
                            'error': f'Failed to stage file {file}: {stage_result.content}',
                            'commit_hash': None,
                            'files_committed': None,
                        }

            # Check if there are any staged changes
            status_result = self.execute('git status --porcelain --cached', self.cwd)
            if status_result.exit_code != 0:
                return {
                    'success': False,
                    'error': f'Failed to check git status: {status_result.content}',
                    'commit_hash': None,
                    'files_committed': None,
                }

            if not status_result.content.strip():
                return {
                    'success': False,
                    'error': 'No staged changes to commit',
                    'commit_hash': None,
                    'files_committed': None,
                }

            # Get list of files to be committed
            files_result = self.execute('git diff --cached --name-only', self.cwd)
            files_committed = (
                files_result.content.strip().split('\n')
                if files_result.exit_code == 0 and files_result.content.strip()
                else []
            )

            # Perform the commit
            commit_result = self.execute(f'git commit -m "{message}"', self.cwd)
            if commit_result.exit_code != 0:
                return {
                    'success': False,
                    'error': f'Failed to commit: {commit_result.content}',
                    'commit_hash': None,
                    'files_committed': None,
                }

            # Get the commit hash
            hash_result = self.execute('git rev-parse HEAD', self.cwd)
            commit_hash = (
                hash_result.content.strip() if hash_result.exit_code == 0 else None
            )

            return {
                'success': True,
                'commit_hash': commit_hash,
                'files_committed': files_committed,
                'output': commit_result.content,
            }

        except Exception as e:
            logger.exception('GitHandler:commit_changes:error', extra={'error': str(e)})
            return {
                'success': False,
                'error': f'Unexpected error during commit: {str(e)}',
                'commit_hash': None,
                'files_committed': None,
            }

    def push_changes(
        self,
        remote: str = 'origin',
        branch: str | None = None,
        force: bool = False,
        set_upstream: bool = False,
    ) -> dict[str, str | bool | None]:
        """
        Pushes commits to a remote git repository.

        Args:
            remote (str): Remote name to push to
            branch (str | None): Branch to push, if None pushes current branch
            force (bool): If True, performs a force push
            set_upstream (bool): If True, sets upstream tracking

        Returns:
            dict: A dictionary containing push information and success status
        """
        if not self.cwd:
            raise ValueError('no_dir_in_git_push')

        try:
            # Get current branch if not specified
            if branch is None:
                branch_result = self.execute('git branch --show-current', self.cwd)
                if branch_result.exit_code != 0:
                    return {
                        'success': False,
                        'error': f'Failed to get current branch: {branch_result.content}',
                        'remote': remote,
                        'branch': None,
                    }
                branch = branch_result.content.strip()

            # Build push command
            push_cmd = 'git push'
            if set_upstream:
                push_cmd += ' -u'
            if force:
                push_cmd += ' --force'
            push_cmd += f' {remote} {branch}'

            # Execute push
            push_result = self.execute(push_cmd, self.cwd)

            # Check for common error patterns
            error_patterns = [
                r'error:',
                r'fatal:',
                r'rejected',
                r'failed to push',
                r'permission denied',
                r'authentication failed',
            ]

            has_error = any(
                re.search(pattern, push_result.content, re.IGNORECASE)
                for pattern in error_patterns
            )

            if push_result.exit_code != 0 or has_error:
                return {
                    'success': False,
                    'error': push_result.content,
                    'remote': remote,
                    'branch': branch,
                }

            return {
                'success': True,
                'output': push_result.content,
                'remote': remote,
                'branch': branch,
            }

        except Exception as e:
            logger.exception('GitHandler:push_changes:error', extra={'error': str(e)})
            return {
                'success': False,
                'error': f'Unexpected error during push: {str(e)}',
                'remote': remote,
                'branch': branch,
            }
