from enum import Enum

from pydantic import BaseModel


class TaskType(str, Enum):
    MERGE_CONFLICTS = 'MERGE_CONFLICTS'
    FAILING_CHECKS = 'FAILING_CHECKS'
    UNRESOLVED_COMMENTS = 'UNRESOLVED_COMMENTS'
    OPEN_ISSUE = 'OPEN_ISSUE'
    OPEN_PR = 'OPEN_PR'


class SuggestedTask(BaseModel):
    task_type: TaskType
    repo: str
    issue_number: int
    title: str


class GitHubUser(BaseModel):
    id: int
    login: str
    avatar_url: str
    company: str | None = None
    name: str | None = None
    email: str | None = None


class GitHubRepository(BaseModel):
    id: int
    full_name: str
    stargazers_count: int | None = None
    link_header: str | None = None


class GhAuthenticationError(ValueError):
    """Raised when there is an issue with GitHub authentication."""

    pass


class GHUnknownException(ValueError):
    """Raised when there is an issue with GitHub communcation."""

    pass
