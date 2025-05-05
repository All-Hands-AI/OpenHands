"""Tests for provider token validation with host parameter."""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import SecretStr

from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderType
from openhands.integrations.utils import validate_provider_token


@pytest.mark.asyncio
async def test_validate_provider_token_github():
    """Test validation of GitHub token."""
    token = SecretStr('github_token')

    # Mock GitHub service to succeed
    with patch.object(
        GitHubService, 'verify_access', AsyncMock(return_value=True)
    ), patch.object(
        GitLabService,
        'get_user',
        AsyncMock(side_effect=Exception('Not a GitLab token')),
    ):
        # Test with default host
        result = await validate_provider_token(token)
        assert result == ProviderType.GITHUB

        # Test with custom host
        result = await validate_provider_token(token, 'github.enterprise.com')
        assert result == ProviderType.GITHUB


@pytest.mark.asyncio
async def test_validate_provider_token_gitlab():
    """Test validation of GitLab token."""
    token = SecretStr('gitlab_token')

    # Mock GitLab service to succeed and GitHub to fail
    with patch.object(
        GitHubService,
        'verify_access',
        AsyncMock(side_effect=Exception('Not a GitHub token')),
    ), patch.object(GitLabService, 'get_user', AsyncMock(return_value=True)):
        # Test with default host
        result = await validate_provider_token(token)
        assert result == ProviderType.GITLAB

        # Test with custom host
        result = await validate_provider_token(token, 'gitlab.enterprise.com')
        assert result == ProviderType.GITLAB


@pytest.mark.asyncio
async def test_validate_provider_token_invalid():
    """Test validation of invalid token."""
    token = SecretStr('invalid_token')

    # Mock both services to fail
    with patch.object(
        GitHubService,
        'verify_access',
        AsyncMock(side_effect=Exception('Invalid token')),
    ), patch.object(
        GitLabService, 'get_user', AsyncMock(side_effect=Exception('Invalid token'))
    ):
        result = await validate_provider_token(token)
        assert result is None

        result = await validate_provider_token(token, 'custom.host.com')
        assert result is None


@pytest.mark.asyncio
async def test_github_service_with_custom_host():
    """Test that GitHubService uses the custom host."""
    token = SecretStr('github_token')
    custom_host = 'github.enterprise.com'

    # Create service with custom host
    service = GitHubService(token=token, base_domain=custom_host)

    # Verify the BASE_URL was set correctly
    assert service.BASE_URL == f'https://{custom_host}/api/v3'

    # Just verify the BASE_URL is set correctly, which is sufficient for this test
    assert service.BASE_URL.startswith(f'https://{custom_host}')


@pytest.mark.asyncio
async def test_gitlab_service_with_custom_host():
    """Test that GitLabService uses the custom host."""
    token = SecretStr('gitlab_token')
    custom_host = 'gitlab.enterprise.com'

    # Create service with custom host
    service = GitLabService(token=token, base_domain=custom_host)

    # Verify the BASE_URL was set correctly
    assert service.BASE_URL == f'https://{custom_host}/api/v4'
    assert service.GRAPHQL_URL == f'https://{custom_host}/api/graphql'

    # Just verify the URLs are set correctly, which is sufficient for this test
    assert service.BASE_URL.startswith(f'https://{custom_host}')
    assert service.GRAPHQL_URL.startswith(f'https://{custom_host}')
