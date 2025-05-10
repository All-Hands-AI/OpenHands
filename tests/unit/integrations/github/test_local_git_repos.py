import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.service_types import ProviderType, Repository
from openhands.server.types import AppMode


@pytest.fixture
def mock_github_service():
    service = GitHubService()
    service._make_request = AsyncMock(return_value=({}, {}))
    service._fetch_paginated_repos = AsyncMock(return_value=[])
    return service


@pytest.fixture
def temp_workspace():
    """Create a temporary directory structure with git repositories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create a git repository in the workspace root
        root_repo_dir = workspace_dir
        os.makedirs(root_repo_dir / '.git')

        # Create a git repository one level deep
        sub_repo_dir = workspace_dir / 'project1'
        os.makedirs(sub_repo_dir)
        os.makedirs(sub_repo_dir / '.git')

        # Create a non-git directory
        non_git_dir = workspace_dir / 'not-a-repo'
        os.makedirs(non_git_dir)

        yield temp_dir


@pytest.mark.asyncio
@patch.dict(os.environ, {'WORKSPACE_BASE': ''})
async def test_get_repositories_without_workspace_base(mock_github_service):
    """Test that get_repositories works without WORKSPACE_BASE set."""
    # Mock the GitHub API response
    mock_github_service._fetch_paginated_repos.return_value = [
        {'id': 1, 'full_name': 'user/repo1', 'stargazers_count': 10, 'private': False}
    ]

    # Call the method
    repos = await mock_github_service.get_repositories('pushed', AppMode.OSS)

    # Verify the result
    assert len(repos) == 1
    assert repos[0].full_name == 'user/repo1'
    assert repos[0].id == 1

    # Verify that _find_git_repositories was not called (since WORKSPACE_BASE is not set)
    mock_github_service._find_git_repositories = MagicMock(return_value=[])
    assert mock_github_service._find_git_repositories.call_count == 0


@pytest.mark.asyncio
@patch.dict(os.environ, {})
async def test_get_repositories_with_workspace_base(
    mock_github_service, temp_workspace
):
    """Test that get_repositories includes local git repositories when WORKSPACE_BASE is set."""
    # Set WORKSPACE_BASE environment variable
    os.environ['WORKSPACE_BASE'] = temp_workspace

    # Mock the GitHub API response
    mock_github_service._fetch_paginated_repos.return_value = [
        {'id': 1, 'full_name': 'user/repo1', 'stargazers_count': 10, 'private': False}
    ]

    # Mock the _find_git_repositories method to return some local repositories
    local_repos = [
        Repository(
            id=12345,
            full_name='local/workspace',
            git_provider=ProviderType.GITHUB,
            is_public=False,
            stargazers_count=0,
        ),
        Repository(
            id=67890,
            full_name='local/project1',
            git_provider=ProviderType.GITHUB,
            is_public=False,
            stargazers_count=0,
        ),
    ]
    mock_github_service._find_git_repositories = MagicMock(return_value=local_repos)

    # Call the method
    repos = await mock_github_service.get_repositories('pushed', AppMode.OSS)

    # Verify the result
    assert len(repos) == 3  # 1 GitHub repo + 2 local repos
    assert repos[0].full_name == 'user/repo1'  # GitHub repo
    assert repos[1].full_name == 'local/workspace'  # Local repo
    assert repos[2].full_name == 'local/project1'  # Local repo

    # Verify that _find_git_repositories was called with the correct path
    mock_github_service._find_git_repositories.assert_called_once_with(temp_workspace)


def test_find_git_repositories(mock_github_service, temp_workspace):
    """Test that _find_git_repositories correctly identifies git repositories."""
    # Call the method
    repos = mock_github_service._find_git_repositories(temp_workspace)

    # Verify the result
    assert len(repos) == 2

    # Verify that the repositories have the expected properties
    repo_names = [repo.full_name for repo in repos]
    assert 'local/project1' in repo_names

    # The root repository should also be found
    workspace_name = Path(temp_workspace).name
    assert f'local/{workspace_name}' in repo_names
