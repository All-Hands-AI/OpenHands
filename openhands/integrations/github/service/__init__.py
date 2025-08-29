from pydantic import SecretStr

from openhands.integrations.github.service.branches_prs import (
    GitHubBranchesMixin,
    GitHubPRsMixin,
)
from openhands.integrations.github.service.graphql import GitHubGraphQLMixin
from openhands.integrations.github.service.microagents import GitHubMicroagentsMixin
from openhands.integrations.github.service.repos import GitHubReposMixin
from openhands.integrations.service_types import (
    BaseGitService,
    GitService,
    InstallationsService,
)


class GitHubService(
    GitHubReposMixin,
    GitHubBranchesMixin,
    GitHubPRsMixin,
    GitHubGraphQLMixin,
    GitHubMicroagentsMixin,
    BaseGitService,
    GitService,
    InstallationsService,
):
    """Assembled GitHub service class combining mixins by feature area."""

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.external_token_manager = external_token_manager

        if token:
            self.token = token

        if base_domain and base_domain != 'github.com':
            self.BASE_URL = f'https://{base_domain}/api/v3'

        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token

    @property
    def provider(self) -> str:
        from openhands.integrations.service_types import ProviderType

        return ProviderType.GITHUB.value
