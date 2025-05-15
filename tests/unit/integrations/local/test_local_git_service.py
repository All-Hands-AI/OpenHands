import os
import tempfile
from pathlib import Path
from types import MappingProxyType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from openhands.integrations.local.local_git_service import LocalGitService
from openhands.integrations.provider import ProviderHandler, ProviderToken
from openhands.integrations.service_types import ProviderType, Repository
from openhands.server.types import AppMode


@pytest.fixture
def mock_local_git_service():
    service = LocalGitService()
    return service


@pytest.fixture
def temp_workspace():
    """Create a temporary directory structure with git repositories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)
        
        # Create a git repository in the workspace root
        root_repo_dir = workspace_dir
        os.makedirs(root_repo_dir / ".git")
        
        # Create a git repository one level deep
        sub_repo_dir = workspace_dir / "project1"
        os.makedirs(sub_repo_dir)
        os.makedirs(sub_repo_dir / ".git")
        
        # Create a non-git directory
        non_git_dir = workspace_dir / "not-a-repo"
        os.makedirs(non_git_dir)
        
        yield temp_dir


@pytest.mark.asyncio
@patch.dict(os.environ, {"WORKSPACE_BASE": ""})
async def test_get_repositories_without_workspace_base(mock_local_git_service):
    """Test that get_repositories returns empty list when WORKSPACE_BASE is not set."""
    # Call the method
    repos = await mock_local_git_service.get_repositories("pushed", AppMode.OSS)
    
    # Verify the result
    assert len(repos) == 0


@pytest.mark.asyncio
@patch.dict(os.environ, {})
async def test_get_repositories_with_workspace_base(mock_local_git_service, temp_workspace):
    """Test that get_repositories includes local git repositories when WORKSPACE_BASE is set."""
    # Set WORKSPACE_BASE environment variable
    os.environ["WORKSPACE_BASE"] = temp_workspace
    
    # Call the method
    repos = await mock_local_git_service.get_repositories("pushed", AppMode.OSS)
    
    # Verify the result
    assert len(repos) == 2  # Root repo and project1 repo
    
    # Verify that the repositories have the expected properties
    repo_names = [repo.full_name for repo in repos]
    assert "local/project1" in repo_names
    
    # The root repository should also be found
    workspace_name = Path(temp_workspace).name
    assert f"local/{workspace_name}" in repo_names
    
    # Verify that all repos have the LOCAL provider type
    for repo in repos:
        assert repo.git_provider == ProviderType.LOCAL


def test_find_git_repositories(mock_local_git_service, temp_workspace):
    """Test that _find_git_repositories correctly identifies git repositories."""
    # Call the method
    repos = mock_local_git_service._find_git_repositories(temp_workspace)
    
    # Verify the result
    assert len(repos) == 2
    
    # Verify that the repositories have the expected properties
    repo_names = [repo.full_name for repo in repos]
    assert "local/project1" in repo_names
    
    # The root repository should also be found
    workspace_name = Path(temp_workspace).name
    assert f"local/{workspace_name}" in repo_names


@pytest.mark.asyncio
@patch.dict(os.environ, {})
async def test_provider_handler_adds_local_provider(temp_workspace):
    """Test that ProviderHandler automatically adds the local git provider when WORKSPACE_BASE is set."""
    # Set WORKSPACE_BASE environment variable
    os.environ["WORKSPACE_BASE"] = temp_workspace
    
    # Create provider tokens without local provider
    provider_tokens = MappingProxyType({
        ProviderType.GITHUB: ProviderToken(token=None, user_id=None, host=None)
    })
    
    # Create provider handler
    handler = ProviderHandler(provider_tokens)
    
    # Verify that the local provider was added
    assert ProviderType.LOCAL in handler.provider_tokens
    
    # Get repositories from all providers
    repos = await handler.get_repositories("pushed", AppMode.OSS)
    
    # Verify that local repositories were found
    assert len(repos) > 0
    
    # Verify that at least some repositories have the LOCAL provider type
    local_repos = [repo for repo in repos if repo.git_provider == ProviderType.LOCAL]
    assert len(local_repos) > 0