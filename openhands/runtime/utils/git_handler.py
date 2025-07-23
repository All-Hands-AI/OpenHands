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
        Recursively retrieves the list of changed files in all Git repositories.
        Uses a single bash command for maximum performance and checks all subdirectories.

        Returns:
            list[dict[str, str]] | None: A list of dictionaries containing file paths and statuses. None if no git repositories found.
        """
        # Use a single command that finds all git repositories and gets their changes
        # This approach uses find to locate .git directories, then processes each one
        base_dir = self.cwd or '.'

        cmd = f"""
        # Find all git repositories and process them, avoiding duplicates
        {{
            # First, find all .git directories
            find "{base_dir}" -name ".git" -type d 2>/dev/null | while read git_dir; do
                echo "$(dirname "$git_dir")"
            done

            # Also check if the base directory itself is a git repo
            if [ -d "{base_dir}/.git" ] || (cd "{base_dir}" && git rev-parse --git-dir >/dev/null 2>&1); then
                echo "{base_dir}"
            fi
        }} | sort -u | while read repo_dir; do
            cd "$repo_dir" || continue

            # Get relative path from base_dir to repo_dir
            if command -v realpath >/dev/null 2>&1; then
                rel_path=$(realpath --relative-to="{base_dir}" "$repo_dir" 2>/dev/null || echo ".")
            else
                rel_path=$(python3 -c "import os; print(os.path.relpath('$repo_dir', '{base_dir}'))" 2>/dev/null || echo ".")
            fi

            # If we're in the base directory, don't add a prefix
            if [ "$rel_path" = "." ]; then
                prefix=""
            else
                prefix="$rel_path/"
            fi

            # Get git status and add prefix to each file path
            git --no-pager status --porcelain=v1 --untracked-files=normal 2>/dev/null | while IFS= read -r line; do
                if [ -n "$line" ] && [ $(echo "$line" | wc -c) -ge 4 ]; then
                    echo "$(echo "$line" | cut -c1-3)$prefix$(echo "$line" | cut -c4-)"
                fi
            done
        done
        """

        output = self.execute(cmd, self.cwd)

        if output.exit_code != 0 or not output.content.strip():
            return None

        result = []
        for line in output.content.splitlines():
            if len(line) < 3:
                continue

            # Git status format: XY filename
            # X = index status, Y = working tree status
            index_status = line[0]
            worktree_status = line[1]
            file_path = line[3:]  # Skip the two status chars and space

            # Determine primary status (prioritize working tree changes)
            if worktree_status != ' ':
                primary_status = worktree_status
            elif index_status != ' ':
                primary_status = index_status
            else:
                continue  # No changes

            # Map git status codes to our expected format
            if primary_status == '?':
                primary_status = 'A'  # Untracked files are treated as added

            result.append(
                {
                    'status': primary_status,
                    'path': file_path,
                }
            )

        return result if result else None

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
