from dataclasses import dataclass
from typing import Callable


@dataclass
class CommandResult:
    content: str
    exit_code: int


class GitHandler:
    def __init__(
        self,
        execute_shell_fn: Callable[[str], CommandResult],
    ):
        self.execute = execute_shell_fn

    def _is_git_repo(self) -> bool:
        cmd = 'git rev-parse --is-inside-work-tree'
        output = self.execute(cmd)
        return output.content.strip() == 'true'

    def _get_current_file_content(self, file_path: str) -> str:
        output = self.execute(f'cat {file_path}')
        return output.content

    def _verify_ref_exists(self, ref: str) -> bool:
        cmd = f'git rev-parse --verify {ref}'
        output = self.execute(cmd)
        return output.exit_code == 0

    def _get_valid_ref(self) -> str | None:
        ref_non_default_branch = f'$(git merge-base HEAD "$(git rev-parse --abbrev-ref origin/{self._get_current_branch()})")'
        ref_default_branch = 'origin/' + self._get_current_branch()
        ref_new_repo = '$(git rev-parse --verify 4b825dc642cb6eb9a060e54bf8d69288fbee4904)'  # compares with empty tree

        refs = [ref_non_default_branch, ref_default_branch, ref_new_repo]
        for ref in refs:
            if self._verify_ref_exists(ref):
                return ref

        return None

    def _get_ref_content(self, file_path: str) -> str:
        ref = self._get_valid_ref()
        if not ref:
            return ''

        cmd = f'git show {ref}:{file_path}'
        output = self.execute(cmd)
        return output.content if output.exit_code == 0 else ''

    def _get_current_branch(self) -> str:
        cmd = 'git remote show origin | grep "HEAD branch"'
        output = self.execute(cmd)
        return output.content.split()[-1].strip()

    def _get_changed_files(self) -> list[str]:
        ref = self._get_valid_ref()
        if not ref:
            return []

        diff_cmd = f'git diff --name-status {ref}'
        output = self.execute(diff_cmd)
        return output.content.splitlines()

    def get_untracked_files(self) -> list[dict[str, str]]:
        cmd = 'git ls-files --others --exclude-standard'
        output = self.execute(cmd)
        obs_list = output.content.splitlines()
        return (
            [{'status': 'A', 'path': path} for path in obs_list]
            if output.exit_code == 0
            else []
        )

    def get_git_changes(self) -> list[dict[str, str]]:
        if not self._is_git_repo():
            raise RuntimeError('Not a git repository')

        result = []
        changes_list = self._get_changed_files()

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

        # join with any untracked files
        result += self.get_untracked_files()
        return result

    def get_git_diff(self, file_path: str) -> dict[str, str]:
        modified = self._get_current_file_content(file_path)
        original = self._get_ref_content(file_path)

        return {
            'modified': modified,
            'original': original,
        }
