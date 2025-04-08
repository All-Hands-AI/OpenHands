from enum import Enum
from typing import Protocol

from pydantic import BaseModel, SecretStr

from openhands.server.types import AppMode


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'


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


class User(BaseModel):
    id: int
    login: str
    avatar_url: str
    company: str | None = None
    name: str | None = None
    email: str | None = None


class Repository(BaseModel):
    id: int
    full_name: str
    git_provider: ProviderType
    stargazers_count: int | None = None
    link_header: str | None = None
    pushed_at: str | None = None  # ISO 8601 format date string


class AuthenticationError(ValueError):
    """Raised when there is an issue with GitHub authentication."""

    pass


class UnknownException(ValueError):
    """Raised when there is an issue with GitHub communcation."""

    pass


class GitService(Protocol):
    """Protocol defining the interface for Git service providers"""

    def __init__(
        self,
        user_id: str | None = None,
        token: SecretStr | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        external_token_manager: bool = False,
    ) -> None:
        """Initialize the service with authentication details"""
        ...

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user"""
        ...

    async def get_user(self) -> User:
        """Get the authenticated user's information"""
        ...

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
    ) -> list[Repository]:
        """Search for repositories"""
        ...

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user"""
        ...
