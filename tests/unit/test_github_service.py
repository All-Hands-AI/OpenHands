from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.service_types import (
    AuthenticationError,
    OwnerType,
    ProviderType,
    Repository,
)
from openhands.server.types import AppMode


@pytest.mark.asyncio
async def test_github_service_token_handling():
    # Test initialization with SecretStr token
    token = SecretStr('test-token')
    service = GitHubService(user_id=None, token=token)
    assert service.token == token
    assert service.token.get_secret_value() == 'test-token'

    # Test headers contain the token correctly
    headers = await service._get_github_headers()
    assert headers['Authorization'] == 'Bearer test-token'
    assert headers['Accept'] == 'application/vnd.github.v3+json'

    # Test initialization without token
    service = GitHubService(user_id='test-user')
    assert service.token == SecretStr('')


@pytest.mark.asyncio
async def test_github_service_token_refresh():
    # Test that token refresh is only attempted when refresh=True
    token = SecretStr('test-token')
    service = GitHubService(user_id=None, token=token)
    assert not service.refresh

    # Test token expiry detection
    assert service._has_token_expired(401)
    assert not service._has_token_expired(200)
    assert not service._has_token_expired(404)

    # Test get_latest_token returns a copy of the current token
    latest_token = await service.get_latest_token()
    assert isinstance(latest_token, SecretStr)
    assert latest_token.get_secret_value() == 'test-token'  # Compare with known value


@pytest.mark.asyncio
async def test_github_service_fetch_data():
    # Mock httpx.AsyncClient for testing API calls
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'login': 'test-user'}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch('httpx.AsyncClient', return_value=mock_client):
        service = GitHubService(user_id=None, token=SecretStr('test-token'))
        _ = await service._make_request('https://api.github.com/user')

        # Verify the request was made with correct headers
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-token'

        # Test error handling with 401 status code
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message='401 Unauthorized', request=Mock(), response=mock_response
        )

        # Reset the mock to test error handling
        mock_client.get.reset_mock()
        mock_client.get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            _ = await service._make_request('https://api.github.com/user')


@pytest.mark.asyncio
async def test_github_get_repositories_with_user_owner_type():
    """Test that get_repositories correctly sets owner_type field for user repositories."""
    service = GitHubService(user_id=None, token=SecretStr('test-token'))

    # Mock repository data for user repositories
    mock_repo_data = [
        {
            'id': 123,
            'full_name': 'test-user/test-repo',
            'private': False,
            'stargazers_count': 10,
            'owner': {'type': 'User'},  # User repository
        },
        {
            'id': 456,
            'full_name': 'test-user/another-repo',
            'private': True,
            'stargazers_count': 5,
            'owner': {'type': 'User'},  # User repository
        },
    ]

    with (
        patch.object(service, '_fetch_paginated_repos', return_value=mock_repo_data),
        patch.object(service, 'get_installation_ids', return_value=[123]),
    ):
        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for user repositories
        for repo in repositories:
            assert repo.owner_type == OwnerType.USER
            assert isinstance(repo, Repository)
            assert repo.git_provider == ProviderType.GITHUB


@pytest.mark.asyncio
async def test_github_get_repositories_with_organization_owner_type():
    """Test that get_repositories correctly sets owner_type field for organization repositories."""
    service = GitHubService(user_id=None, token=SecretStr('test-token'))

    # Mock repository data for organization repositories
    mock_repo_data = [
        {
            'id': 789,
            'full_name': 'test-org/org-repo',
            'private': False,
            'stargazers_count': 25,
            'owner': {'type': 'Organization'},  # Organization repository
        },
        {
            'id': 101,
            'full_name': 'test-org/another-org-repo',
            'private': True,
            'stargazers_count': 15,
            'owner': {'type': 'Organization'},  # Organization repository
        },
    ]

    with (
        patch.object(service, '_fetch_paginated_repos', return_value=mock_repo_data),
        patch.object(service, 'get_installation_ids', return_value=[123]),
    ):
        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for organization repositories
        for repo in repositories:
            assert repo.owner_type == OwnerType.ORGANIZATION
            assert isinstance(repo, Repository)
            assert repo.git_provider == ProviderType.GITHUB


@pytest.mark.asyncio
async def test_github_get_repositories_mixed_owner_types():
    """Test that get_repositories correctly handles mixed user and organization repositories."""
    service = GitHubService(user_id=None, token=SecretStr('test-token'))

    # Mock repository data with mixed owner types
    mock_repo_data = [
        {
            'id': 123,
            'full_name': 'test-user/user-repo',
            'private': False,
            'stargazers_count': 10,
            'owner': {'type': 'User'},  # User repository
        },
        {
            'id': 456,
            'full_name': 'test-org/org-repo',
            'private': True,
            'stargazers_count': 25,
            'owner': {'type': 'Organization'},  # Organization repository
        },
    ]

    with (
        patch.object(service, '_fetch_paginated_repos', return_value=mock_repo_data),
        patch.object(service, 'get_installation_ids', return_value=[123]),
    ):
        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for each repository
        user_repo = next(repo for repo in repositories if 'user-repo' in repo.full_name)
        org_repo = next(repo for repo in repositories if 'org-repo' in repo.full_name)

        assert user_repo.owner_type == OwnerType.USER
        assert org_repo.owner_type == OwnerType.ORGANIZATION


@pytest.mark.asyncio
async def test_github_get_repositories_owner_type_fallback():
    """Test that owner_type defaults to USER when owner type is not 'Organization'."""
    service = GitHubService(user_id=None, token=SecretStr('test-token'))

    # Mock repository data with missing or unexpected owner type
    mock_repo_data = [
        {
            'id': 123,
            'full_name': 'test-user/test-repo',
            'private': False,
            'stargazers_count': 10,
            'owner': {'type': 'User'},  # Explicitly User
        },
        {
            'id': 456,
            'full_name': 'test-user/another-repo',
            'private': True,
            'stargazers_count': 5,
            'owner': {'type': 'Bot'},  # Unexpected type
        },
        {
            'id': 789,
            'full_name': 'test-user/third-repo',
            'private': False,
            'stargazers_count': 15,
            'owner': {},  # Missing type
        },
    ]

    with (
        patch.object(service, '_fetch_paginated_repos', return_value=mock_repo_data),
        patch.object(service, 'get_installation_ids', return_value=[123]),
    ):
        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify all repositories default to USER owner_type
        for repo in repositories:
            assert repo.owner_type == OwnerType.USER
