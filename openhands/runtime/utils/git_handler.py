from dataclasses import dataclass
from typing import Callable


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
    ):
        self.execute = execute_shell_fn
        self.cwd: str | None = None

    def set_cwd(self, cwd: str) -> None:
        """
        Sets the current working directory for Git operations.

        Args:
            cwd (str): The directory path.
        """
        self.cwd = cwd

    def _is_git_repo(self) -> bool:
        """
        Checks if the current directory is a Git repository.

        Returns:
            bool: True if inside a Git repository, otherwise False.
        """
        cmd = 'git --no-pager rev-parse --is-inside-work-tree'
        output = self.execute(cmd, self.cwd)
        return output.content.strip() == 'true'

    def _get_current_file_content(self, file_path: str) -> str:
        """
        Retrieves the current content of a given file.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: The file content.
        """
        output = self.execute(f'cat {file_path}', self.cwd)
        return output.content

    def _verify_ref_exists(self, ref: str) -> bool:
        """
        Verifies whether a specific Git reference exists.

        Args:
            ref (str): The Git reference to check.

        Returns:
            bool: True if the reference exists, otherwise False.
        """
        cmd = f'git --no-pager rev-parse --verify {ref}'
        output = self.execute(cmd, self.cwd)
        return output.exit_code == 0

    def _has_recent_merge_commits(self) -> bool:
        """
        Checks if there are recent merge commits in the current branch.

        Returns:
            bool: True if there are merge commits in the last 10 commits, False otherwise.
        """
        # Check for merge commits in recent history
        cmd = 'git --no-pager rev-list --merges -n 1 HEAD~10..HEAD 2>/dev/null || git --no-pager rev-list --merges -n 1 HEAD'
        output = self.execute(cmd, self.cwd)
        has_merges = output.exit_code == 0 and output.content.strip() != ''

        if has_merges:
            return True

        # Also check if HEAD itself is a merge commit
        cmd = 'git --no-pager rev-list --parents -n 1 HEAD'
        output = self.execute(cmd, self.cwd)
        if output.exit_code == 0:
            # If HEAD has more than one parent, it's a merge commit
            parents = output.content.strip().split()
            return len(parents) > 2  # commit hash + parent1 + parent2 (or more)

        return False

    def _get_valid_ref(self) -> str | None:
        """
        Determines a valid Git reference for comparison.

        Uses merge-base when recent merge commits are detected to show only user changes.
        Otherwise uses origin/current-branch to show changes since last push.

        Returns:
            str | None: A valid Git reference or None if no valid reference is found.
        """
        current_branch = self._get_current_branch()
        default_branch = self._get_default_branch()

        ref_current_branch = f'origin/{current_branch}'
        ref_merge_base = f'$(git --no-pager merge-base HEAD "$(git --no-pager rev-parse --abbrev-ref origin/{default_branch})")'
        ref_default_branch = 'origin/' + default_branch
        ref_new_repo = '$(git --no-pager rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904)'  # compares with empty tree

        # Only use merge-base if:
        # 1. There are recent merge commits AND
        # 2. origin/current-branch would show merged content (is behind after merge)
        if (
            self._has_recent_merge_commits()
            and self._verify_ref_exists(ref_current_branch)
            and self._verify_ref_exists(ref_merge_base)
        ):
            # Check if origin/current-branch is behind (would show merged content)
            cmd = f'git --no-pager rev-list --count {ref_current_branch}..HEAD'
            output = self.execute(cmd, self.cwd)
            if output.exit_code == 0 and int(output.content.strip()) > 0:
                # origin/current-branch is behind, use merge-base to filter merged content
                return ref_merge_base

        # Default behavior: use origin/current-branch first (shows changes since push)
        refs = [
            ref_current_branch,
            ref_merge_base,
            ref_default_branch,
            ref_new_repo,
        ]

        for ref in refs:
            if self._verify_ref_exists(ref):
                return ref

        return None

    def _get_ref_content(self, file_path: str) -> str:
        """
        Retrieves the content of a file from a valid Git reference.

        Args:
            file_path (str): The file path in the repository.

        Returns:
            str: The content of the file from the reference, or an empty string if unavailable.
        """
        ref = self._get_valid_ref()
        if not ref:
            return ''

        cmd = f'git --no-pager show {ref}:{file_path}'
        output = self.execute(cmd, self.cwd)
        return output.content if output.exit_code == 0 else ''

    def _get_default_branch(self) -> str:
        """
        Retrieves the primary Git branch name of the repository.

        Returns:
            str: The name of the primary branch.
        """
        cmd = 'git --no-pager remote show origin | grep "HEAD branch"'
        output = self.execute(cmd, self.cwd)
        return output.content.split()[-1].strip()

    def _get_current_branch(self) -> str:
        """
        Retrieves the currently selected Git branch.

        Returns:
            str: The name of the current branch.
        """
        cmd = 'git --no-pager rev-parse --abbrev-ref HEAD'
        output = self.execute(cmd, self.cwd)
        return output.content.strip()

    def _get_changed_files(self) -> list[str]:
        """
        Retrieves a list of changed files compared to a valid Git reference.

        Returns:
            list[str]: A list of changed file paths.
        """
        ref = self._get_valid_ref()
        if not ref:
            return []

        diff_cmd = f'git --no-pager diff --name-status {ref}'
        output = self.execute(diff_cmd, self.cwd)
        if output.exit_code != 0:
            raise RuntimeError(
                f'Failed to get diff for ref {ref} in {self.cwd}. Command output: {output.content}'
            )
        return output.content.splitlines()

    def _get_untracked_files(self) -> list[dict[str, str]]:
        """
        Retrieves a list of untracked files in the repository. This is useful for detecting new files.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing file paths and statuses.
        """
        cmd = 'git --no-pager ls-files --others --exclude-standard'
        output = self.execute(cmd, self.cwd)
        obs_list = output.content.splitlines()
        return (
            [{'status': 'A', 'path': path} for path in obs_list]
            if output.exit_code == 0
            else []
        )

    def get_git_changes(self) -> list[dict[str, str]] | None:
        """
        Retrieves the list of changed files in the Git repository.

        Returns:
            list[dict[str, str]] | None: A list of dictionaries containing file paths and statuses. None if not a git repository.
        """
        if not self._is_git_repo():
            return None

        changes_list = self._get_changed_files()
        result = parse_git_changes(changes_list)

        # join with any untracked files
        result += self._get_untracked_files()
        return result

    def get_git_diff(self, file_path: str) -> dict[str, str]:
        """
        Retrieves the original and modified content of a file in the repository.

        Args:
            file_path (str): Path to the file.

        Returns:
            dict[str, str]: A dictionary containing the original and modified content.
        """
        modified = self._get_current_file_content(file_path)
        original = self._get_ref_content(file_path)

        return {
            'modified': modified,
            'original': original,
        }


def parse_git_changes(changes_list: list[str]) -> list[dict[str, str]]:
    """
    Parses the list of changed files and extracts their statuses and paths.

    Args:
        changes_list (list[str]): List of changed file entries.

    Returns:
        list[dict[str, str]]: Parsed list of file changes with statuses.
    """
    result = []
    for line in changes_list:
        status = line[:2].strip()
        path = line[2:].strip()

        # Get the first non-space character as the primary status
        primary_status = status.replace(' ', '')[0]
        result.append(
            {
                'status': primary_status,
                'path': path,
            }
        )
    return result
