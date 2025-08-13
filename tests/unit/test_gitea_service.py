"""Tests for Gitea integration."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.gitea.gitea_service import GiteaService
from openhands.integrations.service_types import (
    AuthenticationError,
    Branch,
    OwnerType,
    ProviderType,
    Repository,
    TaskType,
    User,
)
from openhands.server.types import AppMode


@pytest.mark.asyncio
async def test_gitea_service_initialization():
    """Test Gitea service initialization with different configurations."""
    # Test initialization with SecretStr token
    token = SecretStr('test-token')
    service = GiteaService(user_id=None, token=token)
    assert service.token == token
    assert service.token.get_secret_value() == 'test-token'
    assert service.BASE_URL == 'https://gitea.com/api/v1'

    # Test initialization with custom base domain
    service = GiteaService(
        user_id=None, token=token, base_domain='my-gitea.example.com'
    )
    assert service.BASE_URL == 'https://my-gitea.example.com/api/v1'

    # Test initialization with protocol in base domain
    service = GiteaService(
        user_id=None, token=token, base_domain='http://localhost:3000'
    )
    assert service.BASE_URL == 'http://localhost:3000/api/v1'

    # Test initialization without token
    service = GiteaService(user_id='test-user')
    assert service.token == SecretStr('')


@pytest.mark.asyncio
async def test_gitea_service_headers():
    """Test Gitea service header generation."""
    token = SecretStr('test-token')
    service = GiteaService(user_id=None, token=token)

    headers = await service._get_gitea_headers()
    assert headers['Authorization'] == 'token test-token'
    assert headers['Accept'] == 'application/json'
    assert headers['Content-Type'] == 'application/json'
    assert headers['User-Agent'] == 'OpenHands-Gitea-Integration/1.0'

    # Test headers without token
    service = GiteaService(user_id='test-user')
    headers = await service._get_gitea_headers()
    assert 'Authorization' not in headers
    assert headers['Accept'] == 'application/json'


@pytest.mark.asyncio
async def test_gitea_service_token_expiry():
    """Test token expiry detection."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    assert service._has_token_expired(401)
    assert not service._has_token_expired(200)
    assert not service._has_token_expired(404)
    assert not service._has_token_expired(500)


@pytest.mark.asyncio
async def test_gitea_service_make_request():
    """Test the _make_request method with mocked HTTP client."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'login': 'test-user'}
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch('httpx.AsyncClient', return_value=mock_client):
        service = GiteaService(user_id=None, token=SecretStr('test-token'))
        response, headers = await service._make_request('https://gitea.com/api/v1/user')

        assert response == {'login': 'test-user'}
        mock_client.get.assert_called_once()

        # Test error handling with 401 status code
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message='401 Unauthorized', request=Mock(), response=mock_response
        )

        mock_client.get.reset_mock()
        mock_client.get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            await service._make_request('https://gitea.com/api/v1/user')


@pytest.mark.asyncio
async def test_gitea_get_user():
    """Test getting user information."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_user_data = {
        'id': 123,
        'login': 'test-user',
        'avatar_url': 'https://example.com/avatar.png',
        'company': 'Test Company',
        'full_name': 'Test User',
        'email': 'test@example.com',
    }

    with patch.object(service, '_make_request', return_value=(mock_user_data, {})):
        user = await service.get_user()

        assert isinstance(user, User)
        assert user.id == '123'
        assert user.login == 'test-user'
        assert user.avatar_url == 'https://example.com/avatar.png'
        assert user.company == 'Test Company'
        assert user.name == 'Test User'
        assert user.email == 'test@example.com'


@pytest.mark.asyncio
async def test_gitea_search_repositories():
    """Test repository search functionality."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_search_response = {
        'data': [
            {
                'id': 123,
                'full_name': 'test-user/test-repo',
                'private': False,
                'stars_count': 10,
                'updated_at': '2023-01-01T00:00:00Z',
                'owner': {'type': 'User'},
                'default_branch': 'main',
            }
        ]
    }

    with patch.object(
        service, '_make_request', return_value=(mock_search_response, {})
    ):
        repositories = await service.search_repositories(
            query='test', per_page=10, sort='stars', order='desc', public=True
        )

        assert len(repositories) == 1
        repo = repositories[0]
        assert isinstance(repo, Repository)
        assert repo.id == '123'
        assert repo.full_name == 'test-user/test-repo'
        assert repo.git_provider == ProviderType.GITEA
        assert repo.is_public is True
        assert repo.stargazers_count == 10
        assert repo.owner_type == OwnerType.USER


@pytest.mark.asyncio
async def test_gitea_get_all_repositories_user_type():
    """Test getting all repositories with user owner type."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_repos = [
        {
            'id': 123,
            'full_name': 'test-user/user-repo',
            'private': False,
            'stars_count': 10,
            'updated_at': '2023-01-01T00:00:00Z',
            'owner': {'type': 'User'},
            'default_branch': 'main',
        },
        {
            'id': 456,
            'full_name': 'test-user/another-repo',
            'private': True,
            'stars_count': 5,
            'updated_at': '2023-01-02T00:00:00Z',
            'owner': {'type': 'User'},
            'default_branch': 'master',
        },
    ]

    with patch.object(service, '_make_request', return_value=(mock_repos, {})):
        repositories = await service.get_all_repositories('updated', AppMode.SAAS)

        assert len(repositories) == 2
        for repo in repositories:
            assert repo.owner_type == OwnerType.USER
            assert isinstance(repo, Repository)
            assert repo.git_provider == ProviderType.GITEA


@pytest.mark.asyncio
async def test_gitea_get_all_repositories_organization_type():
    """Test getting all repositories with organization owner type."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_repos = [
        {
            'id': 789,
            'full_name': 'test-org/org-repo',
            'private': False,
            'stars_count': 25,
            'updated_at': '2023-01-01T00:00:00Z',
            'owner': {'type': 'Organization'},
            'default_branch': 'main',
        }
    ]

    with patch.object(service, '_make_request', return_value=(mock_repos, {})):
        repositories = await service.get_all_repositories('updated', AppMode.SAAS)

        assert len(repositories) == 1
        repo = repositories[0]
        assert repo.owner_type == OwnerType.ORGANIZATION
        assert isinstance(repo, Repository)
        assert repo.git_provider == ProviderType.GITEA


@pytest.mark.asyncio
async def test_gitea_get_paginated_repos():
    """Test paginated repository retrieval."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_repos = [
        {
            'id': 123,
            'full_name': 'test-user/repo1',
            'private': False,
            'stars_count': 10,
            'updated_at': '2023-01-01T00:00:00Z',
            'owner': {'type': 'User'},
            'default_branch': 'main',
        }
    ]

    with patch.object(service, '_make_request', return_value=(mock_repos, {})):
        repositories = await service.get_paginated_repos(
            page=1, per_page=50, sort='updated', installation_id=None
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'test-user/repo1'


@pytest.mark.asyncio
async def test_gitea_get_suggested_tasks():
    """Test getting suggested tasks from issues and PRs."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    # Mock repositories

    # Mock issues
    mock_issues = [
        {'number': 1, 'title': 'Fix bug in authentication'},
        {'number': 2, 'title': 'Add new feature'},
    ]

    # Mock PRs
    mock_prs = [
        {'number': 3, 'title': 'Update documentation'},
    ]

    with patch.object(
        service,
        'get_all_repositories',
        return_value=[
            Repository(
                id='123',
                full_name='test-user/test-repo',
                git_provider=ProviderType.GITEA,
                is_public=True,
                stargazers_count=10,
                owner_type=OwnerType.USER,
                main_branch='main',
            )
        ],
    ):
        with patch.object(service, '_make_request') as mock_request:
            # First call for issues, second call for PRs
            mock_request.side_effect = [
                (mock_issues, {}),
                (mock_prs, {}),
            ]

            tasks = await service.get_suggested_tasks()

            assert len(tasks) == 3

            # Check issue tasks
            issue_tasks = [t for t in tasks if t.task_type == TaskType.OPEN_ISSUE]
            assert len(issue_tasks) == 2
            assert issue_tasks[0].issue_number == 1
            assert issue_tasks[0].title == 'Fix bug in authentication'
            assert issue_tasks[0].git_provider == ProviderType.GITEA

            # Check PR tasks
            pr_tasks = [t for t in tasks if t.task_type == TaskType.OPEN_PR]
            assert len(pr_tasks) == 1
            assert pr_tasks[0].issue_number == 3
            assert pr_tasks[0].title == 'Update documentation'


@pytest.mark.asyncio
async def test_gitea_get_repository_details():
    """Test getting repository details."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_repo_data = {
        'id': 123,
        'full_name': 'test-user/test-repo',
        'private': False,
        'stars_count': 10,
        'updated_at': '2023-01-01T00:00:00Z',
        'owner': {'type': 'User'},
        'default_branch': 'main',
    }

    with patch.object(service, '_make_request', return_value=(mock_repo_data, {})):
        repository = await service.get_repository_details_from_repo_name(
            'test-user/test-repo'
        )

        assert isinstance(repository, Repository)
        assert repository.id == '123'
        assert repository.full_name == 'test-user/test-repo'
        assert repository.git_provider == ProviderType.GITEA


@pytest.mark.asyncio
async def test_gitea_get_branches():
    """Test getting repository branches."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_branches = [
        {
            'name': 'main',
            'protected': False,
            'commit': {
                'id': 'abc123',
                'timestamp': '2023-01-01T00:00:00Z',
            },
        },
        {
            'name': 'develop',
            'protected': True,
            'commit': {
                'id': 'def456',
                'timestamp': '2023-01-02T00:00:00Z',
            },
        },
        {
            'name': 'feature-branch',
            'protected': False,
            'commit': {},  # Test empty commit object
        },
    ]

    with patch.object(service, '_make_request', return_value=(mock_branches, {})):
        branches = await service.get_branches('test-user/test-repo')

        assert len(branches) == 3

        main_branch = branches[0]
        assert isinstance(main_branch, Branch)
        assert main_branch.name == 'main'
        assert main_branch.commit_sha == 'abc123'
        assert main_branch.protected is False
        assert main_branch.last_push_date == '2023-01-01T00:00:00Z'

        develop_branch = branches[1]
        assert develop_branch.name == 'develop'
        assert develop_branch.protected is True

        # Test branch with empty commit object
        feature_branch = branches[2]
        assert feature_branch.name == 'feature-branch'
        assert feature_branch.commit_sha == ''
        assert feature_branch.last_push_date is None


@pytest.mark.asyncio
async def test_gitea_response_structure_handling():
    """Test handling of different response structures (array vs object with data)."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    # Test array response
    mock_array_response = [
        {
            'id': 123,
            'full_name': 'test-user/test-repo',
            'private': False,
            'stars_count': 10,
            'updated_at': '2023-01-01T00:00:00Z',
            'owner': {'type': 'User'},
            'default_branch': 'main',
        }
    ]

    with patch.object(service, '_make_request', return_value=(mock_array_response, {})):
        repositories = await service.get_all_repositories('updated', AppMode.SAAS)
        assert len(repositories) == 1

    # Test object response with data array
    mock_object_response = {
        'data': [
            {
                'id': 456,
                'full_name': 'test-user/another-repo',
                'private': True,
                'stars_count': 5,
                'updated_at': '2023-01-02T00:00:00Z',
                'owner': {'type': 'User'},
                'default_branch': 'master',
            }
        ]
    }

    with patch.object(
        service, '_make_request', return_value=(mock_object_response, {})
    ):
        repositories = await service.get_all_repositories('updated', AppMode.SAAS)
        assert len(repositories) == 1
        assert repositories[0].id == '456'


@pytest.mark.asyncio
async def test_gitea_suggested_tasks_error_handling():
    """Test error handling in suggested tasks retrieval."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    # Mock repositories
    mock_repos = [
        Repository(
            id='123',
            full_name='test-user/test-repo',
            git_provider=ProviderType.GITEA,
            is_public=True,
            stargazers_count=10,
            owner_type=OwnerType.USER,
            main_branch='main',
        )
    ]

    with patch.object(service, 'get_all_repositories', return_value=mock_repos):
        with patch.object(service, '_make_request', side_effect=Exception('API Error')):
            # Should not raise exception, but return empty list
            tasks = await service.get_suggested_tasks()
            assert tasks == []


@pytest.mark.asyncio
async def test_gitea_suggested_tasks_invalid_data():
    """Test handling of invalid data in suggested tasks."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    mock_repos = [
        Repository(
            id='123',
            full_name='test-user/test-repo',
            git_provider=ProviderType.GITEA,
            is_public=True,
            stargazers_count=10,
            owner_type=OwnerType.USER,
            main_branch='main',
        )
    ]

    # Mock issues with missing required fields
    mock_issues = [
        {'number': 1, 'title': 'Valid issue'},
        {'number': None, 'title': 'Invalid issue - no number'},
        {'number': 2, 'title': None},  # Invalid issue - no title
        {'title': 'Invalid issue - no number field'},
    ]

    mock_prs = [
        {'number': 3, 'title': 'Valid PR'},
        {'number': None, 'title': 'Invalid PR'},
    ]

    with patch.object(service, 'get_all_repositories', return_value=mock_repos):
        with patch.object(service, '_make_request') as mock_request:
            mock_request.side_effect = [
                (mock_issues, {}),
                (mock_prs, {}),
            ]

            tasks = await service.get_suggested_tasks()

            # Should only include valid tasks
            assert len(tasks) == 2
            assert all(task.issue_number is not None for task in tasks)
            assert all(task.title is not None for task in tasks)


@pytest.mark.asyncio
async def test_gitea_pagination_limits():
    """Test pagination limits are properly enforced."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    with patch.object(service, '_make_request') as mock_request:
        mock_request.return_value = ([], {})

        # Test that per_page is limited to 100
        await service.get_paginated_repos(
            page=1, per_page=150, sort='updated', installation_id=None
        )

        # Verify the request was made with limit=100 (Gitea's max)
        call_args = mock_request.call_args
        params = call_args[0][1]  # Second argument is params
        assert params['limit'] == 100


@pytest.mark.asyncio
async def test_gitea_convert_to_repository():
    """Test repository data conversion."""
    service = GiteaService(user_id=None, token=SecretStr('test-token'))

    # Test user repository
    user_repo_data = {
        'id': 123,
        'full_name': 'test-user/test-repo',
        'private': False,
        'stars_count': 10,
        'updated_at': '2023-01-01T00:00:00Z',
        'owner': {'type': 'User'},
        'default_branch': 'main',
    }

    repo = service._convert_to_repository(user_repo_data)
    assert repo.id == '123'
    assert repo.full_name == 'test-user/test-repo'
    assert repo.git_provider == ProviderType.GITEA
    assert repo.is_public is True
    assert repo.stargazers_count == 10
    assert repo.owner_type == OwnerType.USER
    assert repo.main_branch == 'main'

    # Test organization repository
    org_repo_data = {
        'id': 456,
        'full_name': 'test-org/org-repo',
        'private': True,
        'stars_count': 25,
        'updated_at': '2023-01-02T00:00:00Z',
        'owner': {'type': 'Organization'},
        'default_branch': 'develop',
    }

    repo = service._convert_to_repository(org_repo_data)
    assert repo.owner_type == OwnerType.ORGANIZATION
    assert repo.is_public is False
    assert repo.main_branch == 'develop'

    # Test repository with missing optional fields
    minimal_repo_data = {
        'id': 789,
        'full_name': 'test-user/minimal-repo',
        'owner': {},  # Missing type
    }

    repo = service._convert_to_repository(minimal_repo_data)
    assert repo.id == '789'
    assert repo.owner_type == OwnerType.USER  # Default fallback
    assert repo.stargazers_count == 0  # Default value
    assert repo.main_branch == 'main'  # Default value
