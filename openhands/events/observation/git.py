from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class GitCommitObservation(Observation):
    """This data class represents the result of a git commit operation."""

    commit_hash: str | None = None  # The hash of the created commit
    files_committed: list[str] | None = None  # List of files that were committed
    observation: str = ObservationType.COMMIT

    @property
    def error(self) -> bool:
        return self.commit_hash is None

    @property
    def success(self) -> bool:
        return not self.error

    @property
    def message(self) -> str:
        if self.success:
            return f'Successfully committed changes. Commit hash: {self.commit_hash}'
        else:
            return 'Failed to commit changes'

    def __str__(self) -> str:
        ret = f'**GitCommitObservation (source={self.source})**\n'
        if self.commit_hash:
            ret += f'COMMIT HASH: {self.commit_hash}\n'
        if self.files_committed:
            ret += f'FILES COMMITTED: {", ".join(self.files_committed)}\n'
        ret += f'CONTENT:\n{self.content}'
        return ret


@dataclass
class GitPushObservation(Observation):
    """This data class represents the result of a git push operation."""

    remote: str | None = None  # The remote that was pushed to
    branch: str | None = None  # The branch that was pushed
    observation: str = ObservationType.PUSH

    @property
    def error(self) -> bool:
        # Check if the content contains common error indicators
        error_indicators = [
            'error:',
            'fatal:',
            'rejected',
            'failed to push',
            'permission denied',
            'authentication failed',
        ]
        return any(indicator in self.content.lower() for indicator in error_indicators)

    @property
    def success(self) -> bool:
        return not self.error

    @property
    def message(self) -> str:
        if self.success:
            branch_info = f' to {self.branch}' if self.branch else ''
            remote_info = f' on {self.remote}' if self.remote else ''
            return f'Successfully pushed changes{branch_info}{remote_info}'
        else:
            return 'Failed to push changes'

    def __str__(self) -> str:
        ret = f'**GitPushObservation (source={self.source})**\n'
        if self.remote:
            ret += f'REMOTE: {self.remote}\n'
        if self.branch:
            ret += f'BRANCH: {self.branch}\n'
        ret += f'CONTENT:\n{self.content}'
        return ret
