


"""AWS CodeCommit service implementation."""

from __future__ import annotations

from pydantic import SecretStr

from openhands.integrations.codecommit.service.base import CodeCommitBaseMixin
from openhands.integrations.codecommit.service.branches import CodeCommitBranchesMixin
from openhands.integrations.codecommit.service.features import CodeCommitFeaturesMixin
from openhands.integrations.codecommit.service.prs import CodeCommitPRsMixin
from openhands.integrations.codecommit.service.repos import CodeCommitReposMixin
from openhands.integrations.codecommit.service.resolver import CodeCommitResolverMixin
from openhands.integrations.provider import ProviderToken
from openhands.integrations.service_types import GitService


class CodeCommitService(
    CodeCommitBaseMixin,
    CodeCommitReposMixin,
    CodeCommitBranchesMixin,
    CodeCommitPRsMixin,
    CodeCommitFeaturesMixin,
    CodeCommitResolverMixin,
    GitService,
):
    """AWS CodeCommit service implementation."""

    def __init__(
        self,
        token: ProviderToken | SecretStr | None = None,
        base_domain: str | None = None,
    ) -> None:
        """Initialize the CodeCommit service.

        Args:
            token: The AWS access key ID and secret access key
            base_domain: The AWS region
        """
        super().__init__(token=token, base_domain=base_domain)

