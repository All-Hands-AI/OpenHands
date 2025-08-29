from abc import abstractmethod

from pydantic import SecretStr

from openhands.integrations.service_types import BaseGitService, User


class GitHubMixinBase(BaseGitService):
    """Type-support base for GitHub mixins to satisfy static typing.

    Declares common attributes and method signatures used across mixins.
    """

    BASE_URL: str
    token: SecretStr
    refresh: bool
    external_auth_id: str | None

    @abstractmethod
    async def _get_github_headers(self) -> dict: ...

    @abstractmethod
    async def get_user(self) -> User: ...

    @abstractmethod
    async def get_installations(self) -> list[str]: ...
