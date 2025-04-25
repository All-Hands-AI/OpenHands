from pydantic import SecretStr

from openhands.integrations.azuredevops.azuredevops_service import AzureDevOpsService
from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderType


async def validate_provider_token(
    token: SecretStr, base_domain: str | None = None
) -> ProviderType | None:
    """
    Determine whether a token is for GitHub, GitLab, or Azure DevOps by attempting
    to get user info from all services.

    Args:
        token: The token to check

    Returns:
        'github' if it's a GitHub token
        'gitlab' if it's a GitLab token
        'azuredevops' if it's an Azure DevOps token
        None if the token is invalid for all services
    """
    # Try GitHub first
    try:
        github_service = GitHubService(token=token, base_domain=base_domain)
        await github_service.get_user()
        return ProviderType.GITHUB
    except Exception:
        pass

    # Try GitLab next
    try:
        gitlab_service = GitLabService(token=token, base_domain=base_domain)
        await gitlab_service.get_user()
        return ProviderType.GITLAB
    except Exception:
        pass

    # Try Azure DevOps last
    try:
        # For Azure DevOps, we need to try with an organization
        # This will only validate the token format, not access to a specific organization
        azuredevops_service = AzureDevOpsService(token=token)
        await azuredevops_service.get_user()
        return ProviderType.AZUREDEVOPS
    except Exception:
        pass

    return None
