from pydantic import SecretStr

from openhands.integrations.github.service.branches_prs import (
    GitHubBranchesMixin,
    GitHubPRsMixin,
)
from openhands.integrations.github.service.core import GitHubCoreMixin
from openhands.integrations.github.service.graphql import GitHubGraphQLMixin
from openhands.integrations.github.service.http import GitHubHTTPMixin
from openhands.integrations.github.service.installations import (
    GitHubInstallationsMixin,
)
from openhands.integrations.github.service.microagents import GitHubMicroagentsMixin
from openhands.integrations.github.service.repos import GitHubReposMixin
from openhands.integrations.service_types import (
    BaseGitService,
    GitService,
    InstallationsService,
)


class GitHubService(
    GitHubCoreMixin,
    GitHubHTTPMixin,
    GitHubReposMixin,
    GitHubInstallationsMixin,
    GitHubBranchesMixin,
    GitHubPRsMixin,
    GitHubGraphQLMixin,
    GitHubMicroagentsMixin,
    BaseGitService,
    GitService,
    InstallationsService,
):
    """Assembled GitHub service class combining mixins by feature area."""

    # Ensure __init__ from core mixin is available with proper signature
    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
    ) -> None:
        GitHubCoreMixin.__init__(
            self,
            user_id=user_id,
            external_auth_id=external_auth_id,
            external_auth_token=external_auth_token,
            token=token,
            external_token_manager=external_token_manager,
            base_domain=base_domain,
        )
