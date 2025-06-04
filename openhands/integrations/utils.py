import traceback

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderType


async def validate_provider_token(
    token: SecretStr, base_domain: str | None = None
) -> ProviderType | None:
    """
    Determine whether a token is for GitHub or GitLab by attempting to get user info
    from both services.

    Args:
        token: The token to check
        base_domain: Optional base domain for self-hosted instances

    Returns:
        'github' if it's a GitHub token
        'gitlab' if it's a GitLab token
        None if the token is invalid for both services
    """
    # Try GitHub first
    try:
        logger.info(
            f'Attempting to validate GitHub token with base domain: {base_domain or "github.com"}'
        )
        github_service = GitHubService(token=token, base_domain=base_domain)
        await github_service.verify_access()
        logger.info('Successfully validated GitHub token')
        return ProviderType.GITHUB
    except httpx.HTTPStatusError as e:
        logger.warning(
            f'HTTP status error validating GitHub token: {e.response.status_code} - {e.response.reason_phrase}'
        )
        if hasattr(e.response, 'text'):
            logger.warning(f'Response content: {e.response.text}')
    except httpx.HTTPError as e:
        logger.warning(
            f'HTTP error validating GitHub token: {type(e).__name__} - {str(e)}'
        )
    except Exception as e:
        logger.warning(
            f'Failed to validate GitHub token: {e} \n {traceback.format_exc()}'
        )

    # Try GitLab next
    try:
        logger.info(
            f'Attempting to validate GitLab token with base domain: {base_domain or "gitlab.com"}'
        )
        gitlab_service = GitLabService(token=token, base_domain=base_domain)
        await gitlab_service.get_user()
        logger.info('Successfully validated GitLab token')
        return ProviderType.GITLAB
    except httpx.HTTPStatusError as e:
        logger.warning(
            f'HTTP status error validating GitLab token: {e.response.status_code} - {e.response.reason_phrase}'
        )
        if hasattr(e.response, 'text'):
            logger.warning(f'Response content: {e.response.text}')
    except httpx.HTTPError as e:
        logger.warning(
            f'HTTP error validating GitLab token: {type(e).__name__} - {str(e)}'
        )
    except Exception as e:
        logger.warning(
            f'Failed to validate GitLab token: {e} \n {traceback.format_exc()}'
        )

    logger.warning('Token validation failed for both GitHub and GitLab')
    return None
