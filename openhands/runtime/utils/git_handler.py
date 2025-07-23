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

    def _get_valid_ref(self) -> str | None:
        """
        Determines a valid Git reference for comparison.

        Returns:
            str | None: A valid Git reference or None if no valid reference is found.
        """
        current_branch = self._get_current_branch()
        default_branch = self._get_default_branch()

        ref_current_branch = f'origin/{current_branch}'
        ref_non_default_branch = f'$(git --no-pager merge-base HEAD "$(git --no-pager rev-parse --abbrev-ref origin/{default_branch})")'
        ref_default_branch = 'origin/' + default_branch
        ref_new_repo = '$(git --no-pager rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904)'  # compares with empty tree

        refs = [
            ref_current_branch,
            ref_non_default_branch,
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

    def get_git_changes(self) -> list[dict[str, str]] | None:
        """
        Retrieves the list of changed files in Git repositories.
        Examines each direct subdirectory of the workspace directory looking for git repositories
        and returns the changes for each of these directories.
        Optimized to use a single git command per repository for maximum performance.

        Returns:
            list[dict[str, str]] | None: A list of dictionaries containing file paths, statuses, and repository paths. None if no git repositories found.
        """
        # If cwd is not set, return None
        if not self.cwd:
            return None

        # Single bash command that:
        # 1. Creates a list of directories to check (current dir + direct subdirectories)
        # 2. For each directory, checks if it's a git repo and gets status
        # 3. Outputs in format: REPO_PATH|STATUS|FILE_PATH
        cmd = """bash -c '
        {
            # Check current directory first
            echo "."
            # List direct subdirectories (excluding hidden ones)
            find . -maxdepth 1 -type d ! -name ".*" ! -name "." 2>/dev/null || true
        } | while IFS= read -r dir; do
            if [ -d "$dir/.git" ] || git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
                # Get absolute path of the directory
                repo_path=$(cd "$dir" && pwd)
                # Get git status for this repository
                git -C "$dir" status --porcelain 2>/dev/null | while IFS= read -r line; do
                    if [ -n "$line" ]; then
                        # Extract status (first 2 chars) and file path (from char 3 onwards)
                        status=$(echo "$line" | cut -c1-2)
                        file_path=$(echo "$line" | cut -c4-)
                        # Convert status codes to single character
                        case "$status" in
                            "M "*|" M") echo "$repo_path|M|$file_path" ;;
                            "A "*|" A") echo "$repo_path|A|$file_path" ;;
                            "D "*|" D") echo "$repo_path|D|$file_path" ;;
                            "R "*|" R") echo "$repo_path|R|$file_path" ;;
                            "C "*|" C") echo "$repo_path|C|$file_path" ;;
                            "U "*|" U") echo "$repo_path|U|$file_path" ;;
                            "??") echo "$repo_path|A|$file_path" ;;
                            *) echo "$repo_path|M|$file_path" ;;
                        esac
                    fi
                done
            fi
        done
        ' """

        result = self.execute(cmd.strip(), self.cwd)
        if result.exit_code != 0 or not result.content.strip():
            return None

        # Parse the output
        changes = []
        for line in result.content.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) == 3:
                    repo_path, status, file_path = parts
                    if repo_path != self.cwd:
                        file_path = f'{repo_path[len(self.cwd)+1:]}/{file_path}'
                    changes.append(
                        {'status': status, 'path': file_path}
                    )

        return changes if changes else None

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
