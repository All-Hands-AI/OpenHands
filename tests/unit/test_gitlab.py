"""Tests for GitLab integration."""

from unittest.mock import patch

import pytest
from pydantic import SecretStr

from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.service_types import OwnerType, ProviderType, Repository
from openhands.server.types import AppMode


@pytest.mark.asyncio
async def test_gitlab_get_repositories_with_user_owner_type():
    """Test that get_repositories correctly sets owner_type field for user repositories."""
    service = GitLabService(token=SecretStr('test-token'))

    # Mock repository data for user repositories (namespace kind = 'user')
    mock_repos = [
        {
            'id': 123,
            'path_with_namespace': 'test-user/user-repo1',
            'star_count': 10,
            'visibility': 'public',
            'namespace': {'kind': 'user'},  # User namespace
        },
        {
            'id': 456,
            'path_with_namespace': 'test-user/user-repo2',
            'star_count': 5,
            'visibility': 'private',
            'namespace': {'kind': 'user'},  # User namespace
        },
    ]

    with patch.object(service, '_make_request') as mock_request:
        # Mock the pagination response
        mock_request.side_effect = [(mock_repos, {'Link': ''})]  # No next page

        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for user repositories
        for repo in repositories:
            assert repo.owner_type == OwnerType.USER
            assert isinstance(repo, Repository)
            assert repo.git_provider == ProviderType.GITLAB


@pytest.mark.asyncio
async def test_gitlab_get_repositories_with_organization_owner_type():
    """Test that get_repositories correctly sets owner_type field for organization repositories."""
    service = GitLabService(token=SecretStr('test-token'))

    # Mock repository data for organization repositories (namespace kind = 'group')
    mock_repos = [
        {
            'id': 789,
            'path_with_namespace': 'test-org/org-repo1',
            'star_count': 25,
            'visibility': 'public',
            'namespace': {'kind': 'group'},  # Organization/Group namespace
        },
        {
            'id': 101,
            'path_with_namespace': 'test-org/org-repo2',
            'star_count': 15,
            'visibility': 'private',
            'namespace': {'kind': 'group'},  # Organization/Group namespace
        },
    ]

    with patch.object(service, '_make_request') as mock_request:
        # Mock the pagination response
        mock_request.side_effect = [(mock_repos, {'Link': ''})]  # No next page

        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for organization repositories
        for repo in repositories:
            assert repo.owner_type == OwnerType.ORGANIZATION
            assert isinstance(repo, Repository)
            assert repo.git_provider == ProviderType.GITLAB


@pytest.mark.asyncio
async def test_gitlab_get_repositories_mixed_owner_types():
    """Test that get_repositories correctly handles mixed user and organization repositories."""
    service = GitLabService(token=SecretStr('test-token'))

    # Mock repository data with mixed namespace types
    mock_repos = [
        {
            'id': 123,
            'path_with_namespace': 'test-user/user-repo',
            'star_count': 10,
            'visibility': 'public',
            'namespace': {'kind': 'user'},  # User namespace
        },
        {
            'id': 456,
            'path_with_namespace': 'test-org/org-repo',
            'star_count': 25,
            'visibility': 'public',
            'namespace': {'kind': 'group'},  # Organization/Group namespace
        },
    ]

    with patch.object(service, '_make_request') as mock_request:
        # Mock the pagination response
        mock_request.side_effect = [(mock_repos, {'Link': ''})]  # No next page

        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify we got the expected number of repositories
        assert len(repositories) == 2

        # Verify owner_type is correctly set for each repository
        user_repo = next(repo for repo in repositories if 'user-repo' in repo.full_name)
        org_repo = next(repo for repo in repositories if 'org-repo' in repo.full_name)

        assert user_repo.owner_type == OwnerType.USER
        assert org_repo.owner_type == OwnerType.ORGANIZATION


@pytest.mark.asyncio
async def test_gitlab_get_repositories_owner_type_fallback():
    """Test that owner_type defaults to USER when namespace kind is not 'group'."""
    service = GitLabService(token=SecretStr('test-token'))

    # Mock repository data with missing or unexpected namespace kind
    mock_repos = [
        {
            'id': 123,
            'path_with_namespace': 'test-user/user-repo1',
            'star_count': 10,
            'visibility': 'public',
            'namespace': {'kind': 'user'},  # Explicitly user
        },
        {
            'id': 456,
            'path_with_namespace': 'test-user/user-repo2',
            'star_count': 5,
            'visibility': 'private',
            'namespace': {'kind': 'unknown'},  # Unexpected kind
        },
        {
            'id': 789,
            'path_with_namespace': 'test-user/user-repo3',
            'star_count': 15,
            'visibility': 'public',
            'namespace': {},  # Missing kind
        },
    ]

    with patch.object(service, '_make_request') as mock_request:
        # Mock the pagination response
        mock_request.side_effect = [(mock_repos, {'Link': ''})]  # No next page

        repositories = await service.get_repositories('pushed', AppMode.SAAS)

        # Verify all repositories default to USER owner_type
        for repo in repositories:
            assert repo.owner_type == OwnerType.USER
