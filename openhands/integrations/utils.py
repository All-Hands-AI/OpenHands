from pydantic import SecretStr

from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderType


async def validate_provider_token(
    token: SecretStr, base_domain: str | None = None
) -> ProviderType | None:
    """
    Determine whether a token is for GitHub or GitLab.
    Checks GitHub /user, then GitHub /installation/repositories, then GitLab /user.

    Args:
        token: The token to check
        base_domain: Optional base domain for GitHub Enterprise or GitLab self-hosted

    Returns:
        'github' if it's a GitHub token
        'gitlab' if it's a GitLab token
        None if the token is invalid for all checks
    """
    # 1. Try GitHub /user (PAT or user-scoped token)
    try:
        github_service = GitHubService(token=token, base_domain=base_domain)
        await github_service.get_user()
        print('GitHub token validated via /user endpoint.')
        return ProviderType.GITHUB
    except Exception as e:
        print(f'GitHub /user check failed: {e}')

    # 2. Try GitHub /installation/repositories (GitHub App installation token)
    try:
        # Re-initialize or ensure service is still valid if needed
        # Assuming GitHubService instance is okay after previous failure
        await github_service.get_app()
        print('GitHub token validated via /installation/repositories endpoint.')
        return ProviderType.GITHUB
    except Exception as e:
        print(f'GitHub /installation/repositories check failed: {e}')

    # 3. Try GitLab /user
    try:
        gitlab_service = GitLabService(token=token, base_domain=base_domain)
        await gitlab_service.get_user()
        print('GitLab token validated via /user endpoint.')
        return ProviderType.GITLAB
    except Exception as e:  # Catch broader exceptions for GitLab as well
        print(f'GitLab /user check failed: {e}')

    print(
        'Token validation failed for GitHub (/user and /installation/repositories) and GitLab (/user).'
    )
    return None
