from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)


@dataclass
class GitCommitAction(Action):
    """Action for committing changes to the local git repository."""

    commit_message: str  # Commit message
    files: list[str] | None = (
        None  # Specific files to commit, if None commits all staged files
    )
    add_all: bool = False  # If True, stages all changes before committing (git add -A)
    thought: str = ''
    action: str = ActionType.COMMIT
    runnable: ClassVar[bool] = True
    confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    security_risk: ActionSecurityRisk | None = None

    @property
    def message(self) -> str:
        return f'Committing changes: {self.commit_message}'

    def __str__(self) -> str:
        ret = f'**GitCommitAction (source={self.source})**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'COMMIT MESSAGE: {self.commit_message}\n'
        if self.files:
            ret += f'FILES: {", ".join(self.files)}\n'
        if self.add_all:
            ret += 'ADD ALL: True\n'
        return ret


@dataclass
class GitPushAction(Action):
    """Action for pushing commits to a remote git repository."""

    remote: str = 'origin'  # Remote name to push to
    branch: str | None = None  # Branch to push, if None pushes current branch
    force: bool = False  # If True, performs a force push (git push --force)
    set_upstream: bool = False  # If True, sets upstream tracking (git push -u)
    thought: str = ''
    action: str = ActionType.PUSH
    runnable: ClassVar[bool] = True
    confirmation_state: ActionConfirmationStatus = ActionConfirmationStatus.CONFIRMED
    security_risk: ActionSecurityRisk | None = None

    @property
    def message(self) -> str:
        branch_info = f' to {self.branch}' if self.branch else ''
        return f'Pushing changes to {self.remote}{branch_info}'

    def __str__(self) -> str:
        ret = f'**GitPushAction (source={self.source})**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'REMOTE: {self.remote}\n'
        if self.branch:
            ret += f'BRANCH: {self.branch}\n'
        if self.force:
            ret += 'FORCE: True\n'
        if self.set_upstream:
            ret += 'SET UPSTREAM: True\n'
        return ret
