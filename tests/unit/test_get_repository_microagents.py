from types import MappingProxyType
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import quote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.integrations.service_types import (
    AuthenticationError,
    Repository,
)
from openhands.server.routes.git import app as git_app
from openhands.server.user_auth import (
    get_access_token,
    get_provider_tokens,
    get_user_id,
)


@pytest.fixture
def test_client():
    """Create a test client for the git API."""
    app = FastAPI()
    app.include_router(git_app)

    # Override the FastAPI dependencies directly
    def mock_get_provider_tokens():
        return MappingProxyType(
            {
                ProviderType.GITHUB: ProviderToken(
                    token=SecretStr('ghp_test_token'), host='github.com'
                ),
                ProviderType.GITLAB: ProviderToken(
                    token=SecretStr('glpat_test_token'), host='gitlab.com'
                ),
                ProviderType.BITBUCKET: ProviderToken(
                    token=SecretStr('bb_test_token'), host='bitbucket.org'
                ),
            }
        )

    def mock_get_access_token():
        return None

    def mock_get_user_id():
        return 'test_user'

    # Override the dependencies in the app
    app.dependency_overrides[get_provider_tokens] = mock_get_provider_tokens
    app.dependency_overrides[get_access_token] = mock_get_access_token
    app.dependency_overrides[get_user_id] = mock_get_user_id

    yield TestClient(app)


@pytest.fixture
def mock_github_repository():
    """Create a mock GitHub repository for testing."""
    return Repository(
        id='123456',
        full_name='test/repo',
        git_provider=ProviderType.GITHUB,
        is_public=True,
        stargazers_count=100,
    )


@pytest.fixture
def mock_gitlab_repository():
    """Create a mock GitLab repository for testing."""
    return Repository(
        id='123456',
        full_name='test/repo',
        git_provider=ProviderType.GITLAB,
        is_public=True,
        stargazers_count=100,
    )


@pytest.fixture
def mock_bitbucket_repository():
    """Create a mock Bitbucket repository for testing."""
    return Repository(
        id='123456',
        full_name='test/repo',
        git_provider=ProviderType.BITBUCKET,
        is_public=True,
        stargazers_count=100,
    )


@pytest.fixture
def sample_microagent_content():
    """Sample microagent file content."""
    return """---
name: test_agent
type: repo
inputs:
  - name: query
    type: str
    description: Search query for the repository
mcp_tools:
  stdio_servers:
    - name: git
      command: git
    - name: file_editor
      command: editor
---

This is a test repository microagent for testing purposes."""


@pytest.fixture
def sample_cursorrules_content():
    """Sample .cursorrules file content."""
    return """---
name: cursor_rules
type: repo
---

These are cursor rules for the repository."""


class TestGetRepositoryMicroagents:
    """Test cases for the get_repository_microagents API endpoint."""

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_github_success(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_github_repository,
        sample_microagent_content,
        sample_cursorrules_content,
    ):
        """Test successful retrieval of microagents from GitHub repository."""
        # Setup mocks
        mock_verify_repo.return_value = mock_github_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock directory listing response
        directory_response = MagicMock()
        directory_response.status_code = 200
        directory_response.json.return_value = [
            {
                'name': 'test_agent.md',
                'type': 'file',
                'url': 'https://api.github.com/repos/test/repo/contents/.openhands/microagents/test_agent.md',
            }
        ]

        # Mock .cursorrules response
        cursorrules_response = MagicMock()
        cursorrules_response.status_code = 200
        cursorrules_response.json.return_value = {
            'content': 'LS0tCm5hbWU6IGN1cnNvcl9ydWxlcwp0eXBlOiByZXBvCi0tLQoKVGhlc2UgYXJlIGN1cnNvciBydWxlcyBmb3IgdGhlIHJlcG9zaXRvcnku'  # base64 encoded cursorrules content
        }

        # Mock individual file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.json.return_value = {
            'content': 'LS0tCm5hbWU6IHRlc3RfYWdlbnQKdHlwZTogcmVwbwppbnB1dHM6CiAgLSBuYW1lOiBxdWVyeQogICAgdHlwZTogc3RyCiAgICBkZXNjcmlwdGlvbjogU2VhcmNoIHF1ZXJ5IGZvciB0aGUgcmVwb3NpdG9yeQptY3BfdG9vbHM6CiAgc3RkaW9fc2VydmVyczoKICAgIC0gbmFtZTogZ2l0CiAgICAgIGNvbW1hbmQ6IGdpdAogICAgLSBuYW1lOiBmaWxlX2VkaXRvcgogICAgICBjb21tYW5kOiBlZGl0b3IKLS0tCgpUaGlzIGlzIGEgdGVzdCByZXBvc2l0b3J5IG1pY3JvYWdlbnQgZm9yIHRlc3RpbmcgcHVycG9zZXMu'  # base64 encoded microagent content
        }
        file_response.raise_for_status = MagicMock()

        # Configure mock client call sequence
        mock_client.get.side_effect = [
            directory_response,  # Directory listing
            cursorrules_response,  # .cursorrules file
            file_response,  # Individual .md file
        ]

        # Execute test
        response = test_client.get('/api/user/repository/test/repo/microagents')

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # .cursorrules + 1 .md file

        # Check that basic fields are present (content is excluded for performance)
        for microagent in data:
            assert 'name' in microagent
            assert 'path' in microagent
            assert 'git_provider' in microagent
            assert 'created_at' in microagent
            assert microagent['git_provider'] == 'github'
            # Content field should not be present in listing API
            assert 'content' not in microagent
            # Type and other detailed fields are no longer included in listing API
            assert 'type' not in microagent
            assert 'triggers' not in microagent
            assert 'inputs' not in microagent
            assert 'tools' not in microagent

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_gitlab_success(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_gitlab_repository,
    ):
        """Test successful retrieval of microagents from GitLab repository."""
        # Setup mocks
        mock_verify_repo.return_value = mock_gitlab_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock tree response
        tree_response = MagicMock()
        tree_response.status_code = 200
        tree_response.json.return_value = [
            {
                'name': 'test_agent.md',
                'type': 'blob',
                'path': '.openhands/microagents/test_agent.md',
            }
        ]

        # Mock .cursorrules response (404 - not found)
        cursorrules_response = MagicMock()
        cursorrules_response.status_code = 404

        # Mock individual file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.text = """---
name: test_agent
type: repo
inputs:
  - name: query
    type: str
    description: Search query for the repository
mcp_tools:
  stdio_servers:
    - name: git
      command: git
    - name: file_editor
      command: editor
---

This is a test repository microagent for testing purposes."""
        file_response.raise_for_status = MagicMock()

        # Configure mock client call sequence
        mock_client.get.side_effect = [
            tree_response,  # Tree listing
            cursorrules_response,  # .cursorrules file (not found)
            file_response,  # Individual .md file
        ]

        # Execute test
        response = test_client.get('/api/user/repository/test/repo/microagents')

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only 1 .md file
        assert 'content' not in data[0]  # Content should not be present in listing API
        assert data[0]['git_provider'] == 'gitlab'

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_bitbucket_success(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_bitbucket_repository,
    ):
        """Test successful retrieval of microagents from Bitbucket repository."""
        # Setup mocks
        mock_verify_repo.return_value = mock_bitbucket_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock repository info response (to get main branch)
        repo_info_response = MagicMock()
        repo_info_response.status_code = 200
        repo_info_response.json.return_value = {'mainbranch': {'name': 'main'}}
        repo_info_response.raise_for_status = MagicMock()

        # Mock directory listing response
        directory_response = MagicMock()
        directory_response.status_code = 200
        directory_response.json.return_value = {
            'values': [
                {'type': 'commit_file', 'path': '.openhands/microagents/test_agent.md'}
            ]
        }
        directory_response.raise_for_status = MagicMock()

        # Mock .cursorrules response (404 - not found)
        cursorrules_response = MagicMock()
        cursorrules_response.status_code = 404

        # Mock individual file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.text = """---
name: test_agent
type: repo
inputs:
  - name: query
    type: str
    description: Search query for the repository
mcp_tools:
  stdio_servers:
    - name: git
      command: git
    - name: file_editor
      command: editor
---

This is a test repository microagent for testing purposes."""
        file_response.raise_for_status = MagicMock()

        # Configure mock client call sequence
        mock_client.get.side_effect = [
            repo_info_response,  # Repository info
            directory_response,  # Directory listing
            cursorrules_response,  # .cursorrules file (not found)
            file_response,  # Individual .md file
        ]

        # Execute test
        response = test_client.get('/api/user/repository/test/repo/microagents')

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only 1 .md file
        assert 'content' not in data[0]  # Content should not be present in listing API
        assert data[0]['git_provider'] == 'bitbucket'

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_no_directory_found(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_github_repository,
    ):
        """Test when microagents directory is not found."""
        # Setup mocks
        mock_verify_repo.return_value = mock_github_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock 404 response for directory
        directory_response = MagicMock()
        directory_response.status_code = 404

        mock_client.get.return_value = directory_response

        # Execute test
        response = test_client.get('/api/user/repository/test/repo/microagents')

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_authentication_error(
        self,
        mock_verify_repo,
        test_client,
    ):
        """Test authentication error."""
        # Setup mocks
        mock_verify_repo.side_effect = AuthenticationError('Invalid credentials')

        # Execute test
        response = test_client.get('/api/user/repository/test/repo/microagents')

        # Assertions
        assert response.status_code == 401
        assert response.json() == 'Invalid credentials'


class TestGetRepositoryMicroagentContent:
    """Test cases for the get_repository_microagent_content API endpoint."""

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagent_content_github_success(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_github_repository,
        sample_microagent_content,
    ):
        """Test successful retrieval of microagent content from GitHub."""
        # Setup mocks
        mock_verify_repo.return_value = mock_github_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.json.return_value = {
            'content': 'LS0tCm5hbWU6IHRlc3RfYWdlbnQKdHlwZTogcmVwbwppbnB1dHM6CiAgLSBuYW1lOiBxdWVyeQogICAgdHlwZTogc3RyCiAgICBkZXNjcmlwdGlvbjogU2VhcmNoIHF1ZXJ5IGZvciB0aGUgcmVwb3NpdG9yeQptY3BfdG9vbHM6CiAgc3RkaW9fc2VydmVyczoKICAgIC0gbmFtZTogZ2l0CiAgICAgIGNvbW1hbmQ6IGdpdAogICAgLSBuYW1lOiBmaWxlX2VkaXRvcgogICAgICBjb21tYW5kOiBlZGl0b3IKLS0tCgpUaGlzIGlzIGEgdGVzdCByZXBvc2l0b3J5IG1pY3JvYWdlbnQgZm9yIHRlc3RpbmcgcHVycG9zZXMu'  # base64 encoded content
        }
        file_response.raise_for_status = MagicMock()

        mock_client.get.return_value = file_response

        # Execute test
        file_path = '.openhands/microagents/test_agent.md'
        response = test_client.get(
            f'/api/user/repository/test/repo/microagents/content?file_path={quote(file_path)}'
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert 'content' in data
        assert data['content'] == sample_microagent_content
        assert data['path'] == file_path
        assert data['git_provider'] == 'github'

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagent_content_gitlab_success(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_gitlab_repository,
        sample_microagent_content,
    ):
        """Test successful retrieval of microagent content from GitLab."""
        # Setup mocks
        mock_verify_repo.return_value = mock_gitlab_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.text = sample_microagent_content
        file_response.raise_for_status = MagicMock()

        mock_client.get.return_value = file_response

        # Execute test
        file_path = '.openhands/microagents/test_agent.md'
        response = test_client.get(
            f'/api/user/repository/test/repo/microagents/content?file_path={quote(file_path)}'
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['content'] == sample_microagent_content
        assert data['path'] == file_path
        assert data['git_provider'] == 'gitlab'

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagent_content_bitbucket_success(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_bitbucket_repository,
        sample_microagent_content,
    ):
        """Test successful retrieval of microagent content from Bitbucket."""
        # Setup mocks
        mock_verify_repo.return_value = mock_bitbucket_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock repository info response (to get main branch)
        repo_info_response = MagicMock()
        repo_info_response.status_code = 200
        repo_info_response.json.return_value = {'mainbranch': {'name': 'main'}}
        repo_info_response.raise_for_status = MagicMock()

        # Mock file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.text = sample_microagent_content
        file_response.raise_for_status = MagicMock()

        # Configure mock client call sequence
        mock_client.get.side_effect = [
            repo_info_response,  # Repository info
            file_response,  # File content
        ]

        # Execute test
        file_path = '.openhands/microagents/test_agent.md'
        response = test_client.get(
            f'/api/user/repository/test/repo/microagents/content?file_path={quote(file_path)}'
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['content'] == sample_microagent_content
        assert data['path'] == file_path
        assert data['git_provider'] == 'bitbucket'

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagent_content_file_not_found(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_github_repository,
    ):
        """Test when microagent file is not found."""
        # Setup mocks
        mock_verify_repo.return_value = mock_github_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock 404 response
        file_response = MagicMock()
        file_response.status_code = 404

        mock_client.get.return_value = file_response

        # Execute test
        file_path = '.openhands/microagents/nonexistent.md'
        response = test_client.get(
            f'/api/user/repository/test/repo/microagents/content?file_path={quote(file_path)}'
        )

        # Assertions
        assert response.status_code == 500
        assert 'File not found' in response.json()

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagent_content_authentication_error(
        self,
        mock_verify_repo,
        test_client,
    ):
        """Test authentication error for content API."""
        # Setup mocks
        mock_verify_repo.side_effect = AuthenticationError('Invalid credentials')

        # Execute test
        file_path = '.openhands/microagents/test_agent.md'
        response = test_client.get(
            f'/api/user/repository/test/repo/microagents/content?file_path={quote(file_path)}'
        )

        # Assertions
        assert response.status_code == 401
        assert response.json() == 'Invalid credentials'

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagent_content_cursorrules(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
        mock_github_repository,
        sample_cursorrules_content,
    ):
        """Test retrieval of .cursorrules file content."""
        # Setup mocks
        mock_verify_repo.return_value = mock_github_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.json.return_value = {
            'content': 'LS0tCm5hbWU6IGN1cnNvcl9ydWxlcwp0eXBlOiByZXBvCi0tLQoKVGhlc2UgYXJlIGN1cnNvciBydWxlcyBmb3IgdGhlIHJlcG9zaXRvcnku'  # base64 encoded content
        }
        file_response.raise_for_status = MagicMock()

        mock_client.get.return_value = file_response

        # Execute test
        file_path = '.cursorrules'
        response = test_client.get(
            f'/api/user/repository/test/repo/microagents/content?file_path={quote(file_path)}'
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['content'] == sample_cursorrules_content
        assert data['path'] == file_path
        assert data['git_provider'] == 'github'


class TestSpecialRepositoryStructures:
    """Test cases for special repository structures."""

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_openhands_repo_structure(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
    ):
        """Test microagents from .openhands repository structure."""
        # Setup mocks for .openhands repository
        mock_repository = Repository(
            id='123456',
            full_name='test/.openhands',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_verify_repo.return_value = mock_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock directory listing response (should look in 'microagents' folder)
        directory_response = MagicMock()
        directory_response.status_code = 200
        directory_response.json.return_value = [
            {
                'name': 'test_agent.md',
                'type': 'file',
                'url': 'https://api.github.com/repos/test/.openhands/contents/microagents/test_agent.md',
            }
        ]

        # Mock individual file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.json.return_value = {
            'content': 'LS0tCm5hbWU6IHRlc3RfYWdlbnQKdHlwZTogcmVwbwppbnB1dHM6CiAgLSBuYW1lOiBxdWVyeQogICAgdHlwZTogc3RyCiAgICBkZXNjcmlwdGlvbjogU2VhcmNoIHF1ZXJ5IGZvciB0aGUgcmVwb3NpdG9yeQptY3BfdG9vbHM6CiAgc3RkaW9fc2VydmVyczoKICAgIC0gbmFtZTogZ2l0CiAgICAgIGNvbW1hbmQ6IGdpdAogICAgLSBuYW1lOiBmaWxlX2VkaXRvcgogICAgICBjb21tYW5kOiBlZGl0b3IKLS0tCgpUaGlzIGlzIGEgdGVzdCByZXBvc2l0b3J5IG1pY3JvYWdlbnQgZm9yIHRlc3RpbmcgcHVycG9zZXMu'  # base64 encoded content
        }
        file_response.raise_for_status = MagicMock()

        # Mock .cursorrules response (404 - not found)
        cursorrules_response = MagicMock()
        cursorrules_response.status_code = 404

        # Configure mock client call sequence
        mock_client.get.side_effect = [
            directory_response,  # Directory listing
            cursorrules_response,  # .cursorrules file (not found)
            file_response,  # Individual .md file
        ]

        # Execute test
        response = test_client.get('/api/user/repository/test/.openhands/microagents')

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert (
            data[0]['path'] == 'microagents/test_agent.md'
        )  # Should be in microagents folder, not .openhands/microagents

    @pytest.mark.asyncio
    @patch('openhands.server.routes.git.httpx.AsyncClient')
    @patch('openhands.server.routes.git._verify_repository_access')
    async def test_get_microagents_gitlab_openhands_config_structure(
        self,
        mock_verify_repo,
        mock_async_client,
        test_client,
    ):
        """Test microagents from GitLab openhands-config repository structure."""
        # Setup mocks for GitLab openhands-config repository
        mock_repository = Repository(
            id='123456',
            full_name='test/openhands-config',
            git_provider=ProviderType.GITLAB,
            is_public=True,
            stargazers_count=100,
        )
        mock_verify_repo.return_value = mock_repository

        # Mock HTTP client
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client

        # Mock tree response (should look in 'microagents' folder)
        tree_response = MagicMock()
        tree_response.status_code = 200
        tree_response.json.return_value = [
            {
                'name': 'test_agent.md',
                'type': 'blob',
                'path': 'microagents/test_agent.md',
            }
        ]

        # Mock individual file response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.text = """---
name: test_agent
type: repo
inputs:
  - name: query
    type: str
    description: Search query for the repository
mcp_tools:
  stdio_servers:
    - name: git
      command: git
    - name: file_editor
      command: editor
---

This is a test repository microagent for testing purposes."""
        file_response.raise_for_status = MagicMock()

        # Mock .cursorrules response (404 - not found)
        cursorrules_response = MagicMock()
        cursorrules_response.status_code = 404

        # Configure mock client call sequence
        mock_client.get.side_effect = [
            tree_response,  # Tree listing
            cursorrules_response,  # .cursorrules file (not found)
            file_response,  # Individual .md file
        ]

        # Execute test
        response = test_client.get(
            '/api/user/repository/test/openhands-config/microagents'
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert (
            data[0]['path'] == 'microagents/test_agent.md'
        )  # Should be in microagents folder, not .openhands/microagents
        assert data[0]['git_provider'] == 'gitlab'
