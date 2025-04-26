import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import SecretStr

from openhands.integrations.azuredevops.azuredevops_service import AzureDevOpsService
from openhands.integrations.service_types import (
    AuthenticationError,
    ProviderType,
)


@pytest.mark.asyncio
async def test_azuredevops_service_token_handling():
    # Test initialization with SecretStr token
    token = SecretStr('test-token')
    service = AzureDevOpsService(user_id=None, token=token)
    assert service.token == token
    assert service.token.get_secret_value() == 'test-token'

    # Test headers contain the token correctly
    headers = await service._get_azuredevops_headers()
    expected_auth = f'Basic {base64.b64encode(":test-token".encode()).decode()}'
    assert headers['Authorization'] == expected_auth
    assert headers['Content-Type'] == 'application/json'

    # Test initialization without token
    service = AzureDevOpsService(user_id='test-user')
    assert service.token == SecretStr('')


@pytest.mark.asyncio
async def test_azuredevops_service_token_refresh():
    # Test that token refresh is only attempted when refresh=True
    token = SecretStr('test-token')
    service = AzureDevOpsService(user_id=None, token=token)
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
async def test_azuredevops_service_get_user():
    # Mock httpx.AsyncClient for testing API calls
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': 'user-id-123',
        'displayName': 'Test User',
        'emailAddress': 'test@example.com',
        'imageUrl': 'https://example.com/avatar.png',
    }
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch('httpx.AsyncClient', return_value=mock_client):
        service = AzureDevOpsService(user_id=None, token=SecretStr('test-token'))
        user = await service.get_user()

        # Verify the request was made with correct URL and headers
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert (
            call_args[0][0]
            == 'https://dev.azure.com/_apis/profile/profiles/me?api-version=7.0'
        )
        headers = call_args[1]['headers']
        expected_auth = f'Basic {base64.b64encode(":test-token".encode()).decode()}'
        assert headers['Authorization'] == expected_auth

        # Verify user data is correctly parsed
        assert isinstance(user.id, int)
        assert user.login == 'Test User'
        assert user.name == 'Test User'
        assert user.email == 'test@example.com'
        assert user.avatar_url == 'https://example.com/avatar.png'
        assert user.company is None

        # Test error handling with 401 status code
        mock_response.status_code = 401
        mock_client.get.reset_mock()
        mock_client.get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            _ = await service.get_user()


@pytest.mark.asyncio
async def test_azuredevops_service_search_repositories():
    # Mock httpx.AsyncClient for testing API calls
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'value': [
            {
                'id': 'repo-id-1',
                'name': 'test-repo-1',
                'project': {'name': 'TestProject'},
            },
            {
                'id': 'repo-id-2',
                'name': 'test-repo-2',
                'project': {'name': 'TestProject'},
            },
        ]
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch('httpx.AsyncClient', return_value=mock_client):
        service = AzureDevOpsService(
            user_id=None, token=SecretStr('test-token'), organization='testorg'
        )

        repos = await service.search_repositories(
            query='test', per_page=10, sort='updated', order='desc'
        )

        # Verify the request was made with correct URL and headers
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert 'https://dev.azure.com/testorg/_apis/git/repositories' in call_args[0][0]
        assert 'searchCriteria.searchText=test' in call_args[0][0]
        assert 'api-version=7.0' in call_args[0][0]

        # Verify repositories data is correctly parsed
        assert len(repos) == 2
        assert isinstance(repos[0].id, int)
        assert repos[0].full_name == 'testorg/test-repo-1'
        assert repos[0].git_provider == ProviderType.AZUREDEVOPS
        assert isinstance(repos[1].id, int)
        assert repos[1].full_name == 'testorg/test-repo-2'
        assert repos[1].git_provider == ProviderType.AZUREDEVOPS

        # Test with no organization set
        service = AzureDevOpsService(user_id=None, token=SecretStr('test-token'))
        repos = await service.search_repositories(
            query='test', per_page=10, sort='updated', order='desc'
        )
        assert len(repos) == 0


@pytest.mark.asyncio
async def test_azuredevops_service_get_repositories():
    # Mock httpx.AsyncClient for testing API calls
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'value': [
            {
                'id': 'repo-id-1',
                'name': 'test-repo-1',
                'project': {'name': 'TestProject'},
            },
            {
                'id': 'repo-id-2',
                'name': 'test-repo-2',
                'project': {'name': 'TestProject'},
            },
            {
                'id': 'repo-id-3',
                'name': 'test-repo-3',
                'project': {'name': 'TestProject'},
            },
        ]
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch('httpx.AsyncClient', return_value=mock_client):
        service = AzureDevOpsService(
            user_id=None, token=SecretStr('test-token'), organization='testorg'
        )

        repos = await service.get_repositories(sort='updated', installation_id=None)

        # Verify the request was made with correct URL and headers
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert (
            call_args[0][0]
            == 'https://dev.azure.com/testorg/_apis/git/repositories?api-version=7.0'
        )

        # Verify repositories data is correctly parsed
        assert len(repos) == 3
        assert isinstance(repos[0].id, int)
        assert repos[0].full_name == 'testorg/test-repo-1'
        assert repos[0].git_provider == ProviderType.AZUREDEVOPS

        # Test with no organization set
        service = AzureDevOpsService(user_id=None, token=SecretStr('test-token'))
        repos = await service.get_repositories(sort='updated', installation_id=None)
        assert len(repos) == 0
