"""Tests for Bitbucket repository service URL parsing."""

from unittest.mock import patch

import pytest
from pydantic import SecretStr

from openhands.integrations.bitbucket.bitbucket_service import BitBucketService
from openhands.integrations.service_types import OwnerType, Repository
from openhands.integrations.service_types import ProviderType as ServiceProviderType


@pytest.fixture
def bitbucket_service():
    """Create a BitBucketService instance for testing."""
    return BitBucketService(token=SecretStr('test-token'))


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_standard_url(bitbucket_service):
    """Test URL parsing with standard Bitbucket URL."""
    # Mock the get_repository_details_from_repo_name method
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.org/workspace/repo.git',
        html_url='https://bitbucket.org/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test standard Bitbucket URL
        url = 'https://bitbucket.org/workspace/repo'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_with_query_string(
    bitbucket_service,
):
    """Test URL parsing with query string parameters."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.org/workspace/repo.git',
        html_url='https://bitbucket.org/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test URL with query string
        url = 'https://bitbucket.org/workspace/repo?tab=source&at=main'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_with_fragment(bitbucket_service):
    """Test URL parsing with fragment identifier."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.org/workspace/repo.git',
        html_url='https://bitbucket.org/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test URL with fragment
        url = 'https://bitbucket.org/workspace/repo#readme'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_with_extra_path_segments(
    bitbucket_service,
):
    """Test URL parsing with additional path segments."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.org/workspace/repo.git',
        html_url='https://bitbucket.org/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test URL with extra path segments
        url = 'https://bitbucket.org/workspace/repo/src/main/README.md'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_self_hosted(bitbucket_service):
    """Test URL parsing with self-hosted Bitbucket instance."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.company.com/workspace/repo.git',
        html_url='https://bitbucket.company.com/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test self-hosted Bitbucket URL
        url = 'https://bitbucket.company.com/workspace/repo'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_with_port(bitbucket_service):
    """Test URL parsing with port number."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.company.com:8080/workspace/repo.git',
        html_url='https://bitbucket.company.com:8080/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test URL with port
        url = 'https://bitbucket.company.com:8080/workspace/repo'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_complex_url(bitbucket_service):
    """Test URL parsing with complex URL containing query string, fragment, and extra paths."""
    mock_repo = Repository(
        id='1',
        full_name='my-workspace/my-repo',
        name='my-repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.org/my-workspace/my-repo.git',
        html_url='https://bitbucket.org/my-workspace/my-repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test complex URL
        url = 'https://bitbucket.org/my-workspace/my-repo/src/feature-branch/src/main.py?at=feature-branch&fileviewer=file-view-default#lines-25'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'my-workspace/my-repo'
        mock_get_repo.assert_called_once_with('my-workspace/my-repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_invalid_url(bitbucket_service):
    """Test URL parsing with invalid URL."""
    with patch.object(
        bitbucket_service, 'get_repository_details_from_repo_name'
    ) as mock_get_repo:
        # Test invalid URL
        url = 'not-a-valid-url'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        # Should return empty list for invalid URL
        assert len(repositories) == 0
        mock_get_repo.assert_not_called()


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_insufficient_path_segments(
    bitbucket_service,
):
    """Test URL parsing with insufficient path segments."""
    with patch.object(
        bitbucket_service, 'get_repository_details_from_repo_name'
    ) as mock_get_repo:
        # Test URL with only one path segment
        url = 'https://bitbucket.org/workspace'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        # Should return empty list for insufficient path segments
        assert len(repositories) == 0
        mock_get_repo.assert_not_called()


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_empty_path(bitbucket_service):
    """Test URL parsing with empty path."""
    with patch.object(
        bitbucket_service, 'get_repository_details_from_repo_name'
    ) as mock_get_repo:
        # Test URL with empty path
        url = 'https://bitbucket.org/'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        # Should return empty list for empty path
        assert len(repositories) == 0
        mock_get_repo.assert_not_called()


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_trailing_slash(bitbucket_service):
    """Test URL parsing with trailing slash."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='https://bitbucket.org/workspace/repo.git',
        html_url='https://bitbucket.org/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test URL with trailing slash
        url = 'https://bitbucket.org/workspace/repo/'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_http_scheme(bitbucket_service):
    """Test URL parsing with HTTP scheme."""
    mock_repo = Repository(
        id='1',
        full_name='workspace/repo',
        name='repo',
        owner=OwnerType.USER,
        git_provider=ServiceProviderType.BITBUCKET,
        is_public=True,
        clone_url='http://bitbucket.company.com/workspace/repo.git',
        html_url='http://bitbucket.company.com/workspace/repo',
    )

    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        return_value=mock_repo,
    ) as mock_get_repo:
        # Test HTTP URL
        url = 'http://bitbucket.company.com/workspace/repo'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=True
        )

        assert len(repositories) == 1
        assert repositories[0].full_name == 'workspace/repo'
        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_public_url_parsing_exception_handling(
    bitbucket_service,
):
    """Test URL parsing exception handling when get_repository_details_from_repo_name fails."""
    with patch.object(
        bitbucket_service,
        'get_repository_details_from_repo_name',
        side_effect=Exception('API error'),
    ) as mock_get_repo:
        # Test URL that would normally work but API call fails
        url = 'https://bitbucket.org/workspace/repo'

        # The exception should be propagated since it's not caught in the current implementation
        with pytest.raises(Exception, match='API error'):
            await bitbucket_service.search_repositories(
                query=url, per_page=10, sort='updated', order='desc', public=True
            )

        mock_get_repo.assert_called_once_with('workspace/repo')


@pytest.mark.asyncio
async def test_search_repositories_non_public_search(bitbucket_service):
    """Test that non-public search doesn't use URL parsing logic."""
    with (
        patch.object(
            bitbucket_service,
            'get_installations',
            return_value=['workspace1', 'workspace2'],
        ),
        patch.object(
            bitbucket_service, 'get_paginated_repos', return_value=[]
        ) as mock_get_paginated,
    ):
        # Test non-public search with URL-like query
        url = 'https://bitbucket.org/workspace/repo'
        repositories = await bitbucket_service.search_repositories(
            query=url, per_page=10, sort='updated', order='desc', public=False
        )

        # Should not use URL parsing, should use normal search logic
        assert len(repositories) == 0
        # get_paginated_repos should be called for workspace search
        assert mock_get_paginated.call_count > 0
