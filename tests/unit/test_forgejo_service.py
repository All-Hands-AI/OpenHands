from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.forgejo.forgejo_service import ForgejoService
from openhands.integrations.service_types import ProviderType, Repository, User
from openhands.server.types import AppMode


@pytest.fixture
def forgejo_service():
    return ForgejoService(token=SecretStr('test_token'))


@pytest.mark.asyncio
async def test_get_user(forgejo_service):
    # Mock response data
    mock_user_data = {
        'id': 1,
        'username': 'test_user',
        'avatar_url': 'https://codeberg.org/avatar/test_user',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'organization': 'Test Org',
    }

    # Mock the _fetch_data method
    forgejo_service._fetch_data = AsyncMock(return_value=(mock_user_data, {}))

    # Call the method
    user = await forgejo_service.get_user()

    # Verify the result
    assert isinstance(user, User)
    assert user.id == 1
    assert user.login == 'test_user'
    assert user.avatar_url == 'https://codeberg.org/avatar/test_user'
    assert user.name == 'Test User'
    assert user.email == 'test@example.com'
    assert user.company == 'Test Org'

    # Verify the _fetch_data call
    forgejo_service._fetch_data.assert_called_once_with(
        f'{forgejo_service.base_url}/user'
    )


@pytest.mark.asyncio
async def test_search_repositories(forgejo_service):
    # Mock response data
    mock_repos_data = {
        'data': [
            {
                'id': 1,
                'full_name': 'test_user/repo1',
                'stars_count': 10,
            },
            {
                'id': 2,
                'full_name': 'test_user/repo2',
                'stars_count': 20,
            },
        ]
    }

    # Mock the _fetch_data method
    forgejo_service._fetch_data = AsyncMock(return_value=(mock_repos_data, {}))

    # Call the method
    repos = await forgejo_service.search_repositories('test', 10, 'updated', 'desc')

    # Verify the result
    assert len(repos) == 2
    assert all(isinstance(repo, Repository) for repo in repos)
    assert repos[0].id == 1
    assert repos[0].full_name == 'test_user/repo1'
    assert repos[0].stargazers_count == 10
    assert repos[0].git_provider == ProviderType.FORGEJO
    assert repos[1].id == 2
    assert repos[1].full_name == 'test_user/repo2'
    assert repos[1].stargazers_count == 20
    assert repos[1].git_provider == ProviderType.FORGEJO

    # Verify the _fetch_data call
    forgejo_service._fetch_data.assert_called_once_with(
        f'{forgejo_service.base_url}/repos/search',
        {
            'q': 'test',
            'limit': 10,
            'sort': 'updated',
            'order': 'desc',
            'mode': 'source',
        },
    )


@pytest.mark.asyncio
async def test_get_repositories(forgejo_service):
    # Mock response data for first page
    mock_repos_data_page1 = [
        {
            'id': 1,
            'full_name': 'test_user/repo1',
            'stars_count': 10,
        },
        {
            'id': 2,
            'full_name': 'test_user/repo2',
            'stars_count': 20,
        },
    ]

    # Mock response data for second page
    mock_repos_data_page2 = [
        {
            'id': 3,
            'full_name': 'test_user/repo3',
            'stars_count': 30,
        },
    ]

    # Mock the _fetch_data method to return different data for different pages
    forgejo_service._fetch_data = AsyncMock()
    forgejo_service._fetch_data.side_effect = [
        (
            mock_repos_data_page1,
            {'Link': '<https://codeberg.org/api/v1/user/repos?page=2>; rel="next"'},
        ),
        (mock_repos_data_page2, {'Link': ''}),
    ]

    # Call the method
    repos = await forgejo_service.get_repositories('updated', AppMode.OSS)

    # Verify the result
    assert len(repos) == 3
    assert all(isinstance(repo, Repository) for repo in repos)
    assert repos[0].id == 1
    assert repos[0].full_name == 'test_user/repo1'
    assert repos[0].stargazers_count == 10
    assert repos[0].git_provider == ProviderType.FORGEJO
    assert repos[1].id == 2
    assert repos[1].full_name == 'test_user/repo2'
    assert repos[1].stargazers_count == 20
    assert repos[1].git_provider == ProviderType.FORGEJO
    assert repos[2].id == 3
    assert repos[2].full_name == 'test_user/repo3'
    assert repos[2].stargazers_count == 30
    assert repos[2].git_provider == ProviderType.FORGEJO

    # Verify the _fetch_data calls
    assert forgejo_service._fetch_data.call_count == 2
    forgejo_service._fetch_data.assert_any_call(
        f'{forgejo_service.base_url}/user/repos',
        {'page': '1', 'limit': '100', 'sort': 'updated'},
    )
    forgejo_service._fetch_data.assert_any_call(
        f'{forgejo_service.base_url}/user/repos',
        {'page': '2', 'limit': '100', 'sort': 'updated'},
    )


@pytest.mark.asyncio
async def test_fetch_data_success(forgejo_service):
    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {'key': 'value'}
    mock_response.headers = {'Link': 'next_link'}
    mock_client.__aenter__.return_value.get.return_value = mock_response

    # Patch httpx.AsyncClient
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call the method
        result, headers = await forgejo_service._fetch_data(
            'https://test.url', {'param': 'value'}
        )

    # Verify the result
    assert result == {'key': 'value'}
    assert headers == {'Link': 'next_link'}
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_data_auth_error(forgejo_service):
    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        '401 Unauthorized', request=MagicMock(), response=mock_response
    )
    mock_client.__aenter__.return_value.get.return_value = mock_response

    # Patch httpx.AsyncClient
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call the method and expect an exception
        with pytest.raises(Exception) as excinfo:
            await forgejo_service._fetch_data('https://test.url', {'param': 'value'})

    # Verify the exception
    assert 'Invalid Forgejo token' in str(excinfo.value)


@pytest.mark.asyncio
async def test_fetch_data_other_error(forgejo_service):
    # Mock httpx.AsyncClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        '500 Server Error', request=MagicMock(), response=mock_response
    )
    mock_client.__aenter__.return_value.get.return_value = mock_response

    # Patch httpx.AsyncClient
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call the method and expect an exception
        with pytest.raises(Exception) as excinfo:
            await forgejo_service._fetch_data('https://test.url', {'param': 'value'})

    # Verify the exception
    assert 'Unknown error' in str(excinfo.value)
