from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.bitbucket.bitbucket_service import BitBucketService
from openhands.integrations.codecommit.codecommit_service import CodeCommitService
from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderToken, ProviderType


async def validate_provider_token(
    token: SecretStr | ProviderToken, base_domain: str | None = None
) -> ProviderType | None:
    """Determine whether a token is for GitHub, GitLab, Bitbucket, or CodeCommit by attempting to get user info
    from the services.

    Args:
        token: The token to check (SecretStr or ProviderToken with optional secret field for AWS)
        base_domain: Optional base domain for the service

    Returns:
        'github' if it's a GitHub token
        'gitlab' if it's a GitLab token
        'bitbucket' if it's a Bitbucket token
        'codecommit' if it's an AWS CodeCommit token
        None if the token is invalid for all services
    """
    # Skip validation for empty tokens
    if token is None:
        return None  # type: ignore[unreachable]

    # Convert ProviderToken to SecretStr if needed
    secret_key = None
    if isinstance(token, ProviderToken):
        secret_key = token.secret
        token = token.token or SecretStr('')
        if token is None:
            return None  # type: ignore[unreachable]

    # Try GitHub first
    github_error = None
    try:
        github_service = GitHubService(token=token, base_domain=base_domain)
        await github_service.verify_access()
        return ProviderType.GITHUB
    except Exception as e:
        github_error = e

    # Try GitLab next
    gitlab_error = None
    try:
        gitlab_service = GitLabService(token=token, base_domain=base_domain)
        await gitlab_service.get_user()
        return ProviderType.GITLAB
    except Exception as e:
        gitlab_error = e

    # Try Bitbucket next
    bitbucket_error = None
    try:
        bitbucket_service = BitBucketService(token=token, base_domain=base_domain)
        await bitbucket_service.get_user()
        return ProviderType.BITBUCKET
    except Exception as e:
        bitbucket_error = e
        
    # Try CodeCommit last
    codecommit_error = None
    try:
        # For CodeCommit, we need both access key and secret key
        provider_token = ProviderToken(token=token, secret=secret_key, host=base_domain)
        codecommit_service = CodeCommitService(token=provider_token, base_domain=base_domain)
        await codecommit_service.get_user()
        return ProviderType.CODECOMMIT
    except Exception as e:
        codecommit_error = e

    logger.debug(
        f'Failed to validate token: {github_error} \n {gitlab_error} \n {bitbucket_error} \n {codecommit_error}'
    )

    return None
