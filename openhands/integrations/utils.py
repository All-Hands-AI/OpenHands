import traceback

from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.bitbucket.bitbucket_service import BitbucketService
from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderType


async def validate_provider_token(
    token: SecretStr, base_domain: str | None = None
) -> ProviderType | None:
    """
    Determine whether a token is for GitHub, GitLab, or Bitbucket by attempting to get user info
    from the services.

    Args:
        token: The token to check
        base_domain: Optional base domain for the service

    Returns:
        'github' if it's a GitHub token
        'gitlab' if it's a GitLab token
        'bitbucket' if it's a Bitbucket token
        None if the token is invalid for all services
    """
    # Skip validation for empty tokens
    if token is None or not token.get_secret_value().strip():
        return None
        
    # Try GitHub first
    try:
        github_service = GitHubService(token=token, base_domain=base_domain)
        await github_service.verify_access()
        return ProviderType.GITHUB
    except Exception as e:
        logger.debug(
            f'Failed to validate Github token: {e} \n {traceback.format_exc()}'
        )

    # Try GitLab next
    try:
        gitlab_service = GitLabService(token=token, base_domain=base_domain)
        await gitlab_service.get_user()
        return ProviderType.GITLAB
    except Exception as e:
        logger.debug(
            f'Failed to validate GitLab token: {e} \n {traceback.format_exc()}'
        )

    # Try Bitbucket last
    try:
        bitbucket_service = BitbucketService(token=token, base_domain=base_domain)
        await bitbucket_service.get_user()
        return ProviderType.BITBUCKET
    except Exception as e:
        logger.debug(
            f'Failed to validate Bitbucket token: {e} \n {traceback.format_exc()}'
        )

    return None
