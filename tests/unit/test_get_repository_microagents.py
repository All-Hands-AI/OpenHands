import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig
from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.integrations.service_types import (
    AuthenticationError,
    Repository,
)
from openhands.microagent.microagent import KnowledgeMicroagent, RepoMicroagent
from openhands.microagent.types import InputMetadata, MicroagentMetadata, MicroagentType
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

    # Mock SESSION_API_KEY to None to disable authentication in tests
    with patch.dict(os.environ, {'SESSION_API_KEY': ''}, clear=False):
        # Clear the SESSION_API_KEY to disable auth dependency
        with patch('openhands.server.dependencies._SESSION_API_KEY', None):
            # Override the FastAPI dependencies directly
            def mock_get_provider_tokens():
                return {
                    ProviderType.GITHUB: ProviderToken(
                        token=SecretStr('ghp_test_token'), host='github.com'
                    )
                }

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
def mock_provider_tokens():
    """Create mock provider tokens for testing."""
    return {
        ProviderType.GITHUB: ProviderToken(
            token=SecretStr('ghp_test_token'), host='github.com'
        ),
        ProviderType.GITLAB: ProviderToken(
            token=SecretStr('glpat_test_token'), host='gitlab.com'
        ),
        ProviderType.BITBUCKET: ProviderToken(
            token=SecretStr('test_token'), host='bitbucket.org'
        ),
    }


@pytest.fixture
def mock_repo_microagent():
    """Create a mock repository microagent."""
    return RepoMicroagent(
        name='test_repo_agent',
        content='This is a test repository microagent for testing purposes.',
        metadata=MicroagentMetadata(
            name='test_repo_agent',
            type=MicroagentType.REPO_KNOWLEDGE,
            inputs=[
                InputMetadata(
                    name='query',
                    type='str',
                    description='Search query for the repository',
                )
            ],
            mcp_tools=MCPConfig(
                stdio_servers=[
                    MCPStdioServerConfig(name='git', command='git'),
                    MCPStdioServerConfig(name='file_editor', command='editor'),
                ]
            ),
        ),
        source='test_source',
        type=MicroagentType.REPO_KNOWLEDGE,
    )


@pytest.fixture
def mock_knowledge_microagent():
    """Create a mock knowledge microagent."""
    return KnowledgeMicroagent(
        name='test_knowledge_agent',
        content='This is a test knowledge microagent for testing purposes.',
        metadata=MicroagentMetadata(
            name='test_knowledge_agent',
            type=MicroagentType.KNOWLEDGE,
            inputs=[
                InputMetadata(
                    name='topic', type='str', description='Topic to search for'
                )
            ],
            mcp_tools=MCPConfig(
                stdio_servers=[
                    MCPStdioServerConfig(name='search', command='search'),
                    MCPStdioServerConfig(name='fetch', command='fetch'),
                ]
            ),
        ),
        source='test_source',
        type=MicroagentType.KNOWLEDGE,
        triggers=['test', 'knowledge', 'search'],
    )


@pytest.fixture
def temp_microagents_dir():
    """Create a temporary directory with microagents for testing."""
    temp_dir = tempfile.mkdtemp()
    microagents_dir = Path(temp_dir) / 'repo' / '.openhands' / 'microagents'
    microagents_dir.mkdir(parents=True, exist_ok=True)

    # Create sample microagent files
    repo_agent_file = microagents_dir / 'test_repo_agent.md'
    repo_agent_file.write_text(
        """---
name: test_repo_agent
type: repo_knowledge
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

This is a test repository microagent for testing purposes.
"""
    )

    knowledge_agent_file = microagents_dir / 'test_knowledge_agent.md'
    knowledge_agent_file.write_text(
        """---
name: test_knowledge_agent
type: knowledge
triggers: [test, knowledge, search]
inputs:
  - name: topic
    type: str
    description: Topic to search for
mcp_tools:
  stdio_servers:
    - name: search
      command: search
    - name: fetch
      command: fetch
---

This is a test knowledge microagent for testing purposes.
"""
    )

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestGetRepositoryMicroagents:
    """Test cases for the get_repository_microagents API endpoint."""

    @pytest.mark.asyncio
    async def test_get_microagents_success(
        self,
        test_client,
        mock_provider_tokens,
        mock_repo_microagent,
        mock_knowledge_microagent,
        temp_microagents_dir,
    ):
        """Test successful retrieval of microagents from a repository."""
        # Override the default provider tokens with the mock ones
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run for git clone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ''

        # Mock load_microagents_from_dir
        mock_repo_agents = {'test_repo_agent': mock_repo_microagent}
        mock_knowledge_agents = {'test_knowledge_agent': mock_knowledge_microagent}

        with patch(
            'openhands.server.routes.git.ProviderHandler',
            return_value=mock_provider_handler,
        ):
            with patch(
                'openhands.server.routes.git.subprocess.run',
                return_value=mock_result,
            ):
                with patch(
                    'openhands.server.routes.git.load_microagents_from_dir',
                    return_value=(mock_repo_agents, mock_knowledge_agents),
                ):
                    with patch(
                        'openhands.server.routes.git.tempfile.mkdtemp',
                        return_value=temp_microagents_dir,
                    ):
                        with patch(
                            'openhands.server.routes.git._get_file_creation_time',
                            return_value=datetime.now(),
                        ):
                            response = test_client.get(
                                '/api/user/repository/test/repo/microagents'
                            )

                            assert response.status_code == 200
                            data = response.json()
                            assert len(data) == 2

                            # Check repo microagent
                            repo_agent = next(
                                m for m in data if m['name'] == 'test_repo_agent'
                            )
                            assert repo_agent['type'] == 'repo'
                            assert (
                                repo_agent['content']
                                == 'This is a test repository microagent for testing purposes.'
                            )
                            assert repo_agent['triggers'] == []
                            assert len(repo_agent['inputs']) == 1
                            assert repo_agent['inputs'][0]['name'] == 'query'
                            assert repo_agent['tools'] == ['git', 'file_editor']
                            assert 'created_at' in repo_agent
                            assert 'git_provider' in repo_agent
                            assert repo_agent['git_provider'] == 'github'

                            # Check knowledge microagent - using actual returned triggers
                            knowledge_agent = next(
                                m for m in data if m['name'] == 'test_knowledge_agent'
                            )
                            assert knowledge_agent['type'] == 'knowledge'
                            assert (
                                knowledge_agent['content']
                                == 'This is a test knowledge microagent for testing purposes.'
                            )
                            # The triggers come from the actual microagent object
                            assert (
                                knowledge_agent['triggers']
                                == mock_knowledge_microagent.triggers
                            )
                            assert len(knowledge_agent['inputs']) == 1
                            assert knowledge_agent['inputs'][0]['name'] == 'topic'
                            assert knowledge_agent['tools'] == [
                                'search',
                                'fetch',
                            ]
                            assert 'created_at' in knowledge_agent
                            assert 'git_provider' in knowledge_agent
                            assert knowledge_agent['git_provider'] == 'github'

    @pytest.mark.asyncio
    async def test_get_microagents_no_provider_tokens(self, test_client):
        """Test error when no provider tokens are provided."""
        # Override the dependency to return None to simulate no provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = lambda: None

        response = test_client.get('/api/user/repository/test/repo/microagents')

        assert response.status_code == 401
        assert 'Git provider token required' in response.json()

    @pytest.mark.asyncio
    async def test_get_microagents_authentication_error(
        self, test_client, mock_provider_tokens
    ):
        """Test authentication error when verifying repository."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler to raise AuthenticationError
        mock_provider_handler = MagicMock()
        mock_provider_handler.verify_repo_provider = AsyncMock(
            side_effect=AuthenticationError('Invalid credentials')
        )

        with patch(
            'openhands.server.routes.git.ProviderHandler',
            return_value=mock_provider_handler,
        ):
            response = test_client.get('/api/user/repository/test/repo/microagents')

            assert response.status_code == 401
            assert response.json() == 'Invalid credentials'

    @pytest.mark.asyncio
    async def test_get_microagents_clone_failure(
        self, test_client, mock_provider_tokens
    ):
        """Test error when git clone fails."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run to fail
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = 'Repository not found'

        with patch(
            'openhands.server.routes.git.ProviderHandler',
            return_value=mock_provider_handler,
        ):
            with patch(
                'openhands.server.routes.git.subprocess.run',
                return_value=mock_result,
            ):
                response = test_client.get('/api/user/repository/test/repo/microagents')

                assert response.status_code == 500
                assert 'Failed to clone repository' in response.json()

    @pytest.mark.asyncio
    async def test_get_microagents_no_microagents_directory(
        self, test_client, mock_provider_tokens
    ):
        """Test when repository has no .openhands/microagents directory."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run for successful clone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ''

        # Create temporary directory without microagents
        temp_dir = tempfile.mkdtemp()
        repo_dir = Path(temp_dir) / 'repo'
        repo_dir.mkdir(exist_ok=True)

        try:
            with patch(
                'openhands.server.routes.git.ProviderHandler',
                return_value=mock_provider_handler,
            ):
                with patch(
                    'openhands.server.routes.git.subprocess.run',
                    return_value=mock_result,
                ):
                    with patch(
                        'openhands.server.routes.git.tempfile.mkdtemp',
                        return_value=temp_dir,
                    ):
                        response = test_client.get(
                            '/api/user/repository/test/repo/microagents'
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data == []
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_microagents_empty_directory(
        self, test_client, mock_provider_tokens
    ):
        """Test when microagents directory exists but is empty."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run for successful clone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ''

        # Mock load_microagents_from_dir to return empty results
        mock_repo_agents = {}
        mock_knowledge_agents = {}

        with patch(
            'openhands.server.routes.git.ProviderHandler',
            return_value=mock_provider_handler,
        ):
            with patch(
                'openhands.server.routes.git.subprocess.run',
                return_value=mock_result,
            ):
                with patch(
                    'openhands.server.routes.git.load_microagents_from_dir',
                    return_value=(mock_repo_agents, mock_knowledge_agents),
                ):
                    response = test_client.get(
                        '/api/user/repository/test/repo/microagents'
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data == []

    @pytest.mark.asyncio
    async def test_get_microagents_different_providers(
        self, test_client, mock_repo_microagent
    ):
        """Test microagents endpoint with GitHub provider."""
        # Test specifically with GitHub provider
        provider_tokens = {
            ProviderType.GITHUB: ProviderToken(
                token=SecretStr('ghp_test_token'), host='github.com'
            )
        }

        # Override the dependency to use specific provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: provider_tokens
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run for successful clone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ''

        # Create temporary directory with microagents
        temp_dir = tempfile.mkdtemp()
        microagents_dir = Path(temp_dir) / 'repo' / '.openhands' / 'microagents'
        microagents_dir.mkdir(parents=True, exist_ok=True)

        # Mock load_microagents_from_dir
        mock_repo_agents = {'test_repo_agent': mock_repo_microagent}
        mock_knowledge_agents = {}

        try:
            with patch(
                'openhands.server.routes.git.ProviderHandler',
                return_value=mock_provider_handler,
            ):
                with patch(
                    'openhands.server.routes.git.subprocess.run',
                    return_value=mock_result,
                ):
                    with patch(
                        'openhands.server.routes.git.load_microagents_from_dir',
                        return_value=(
                            mock_repo_agents,
                            mock_knowledge_agents,
                        ),
                    ):
                        with patch(
                            'openhands.server.routes.git.tempfile.mkdtemp',
                            return_value=temp_dir,
                        ):
                            with patch(
                                'openhands.server.routes.git._get_file_creation_time',
                                return_value=datetime.now(),
                            ):
                                response = test_client.get(
                                    '/api/user/repository/test/repo/microagents'
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert len(data) == 1
                                assert data[0]['name'] == 'test_repo_agent'
                                assert data[0]['type'] == 'repo'
                                assert 'created_at' in data[0]
                                assert 'git_provider' in data[0]
                                assert data[0]['git_provider'] == 'github'
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_microagents_with_external_auth(
        self, test_client, mock_provider_tokens, mock_repo_microagent
    ):
        """Test microagents endpoint with external authentication."""
        # Override the dependencies to use external auth
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )
        test_client.app.dependency_overrides[get_access_token] = lambda: SecretStr(
            'external_token'
        )
        test_client.app.dependency_overrides[get_user_id] = lambda: 'external_user'

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run for successful clone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ''

        # Create temporary directory with microagents
        temp_dir = tempfile.mkdtemp()
        microagents_dir = Path(temp_dir) / 'repo' / '.openhands' / 'microagents'
        microagents_dir.mkdir(parents=True, exist_ok=True)

        # Mock load_microagents_from_dir
        mock_repo_agents = {'test_repo_agent': mock_repo_microagent}
        mock_knowledge_agents = {}

        try:
            with patch(
                'openhands.server.routes.git.ProviderHandler',
                return_value=mock_provider_handler,
            ):
                with patch(
                    'openhands.server.routes.git.subprocess.run',
                    return_value=mock_result,
                ):
                    with patch(
                        'openhands.server.routes.git.load_microagents_from_dir',
                        return_value=(
                            mock_repo_agents,
                            mock_knowledge_agents,
                        ),
                    ):
                        with patch(
                            'openhands.server.routes.git.tempfile.mkdtemp',
                            return_value=temp_dir,
                        ):
                            with patch(
                                'openhands.server.routes.git._get_file_creation_time',
                                return_value=datetime.now(),
                            ):
                                response = test_client.get(
                                    '/api/user/repository/test/repo/microagents'
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert len(data) == 1
                                assert data[0]['name'] == 'test_repo_agent'
                                assert 'created_at' in data[0]
                                assert 'git_provider' in data[0]
                                assert data[0]['git_provider'] == 'github'
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_microagents_generic_exception(
        self, test_client, mock_provider_tokens
    ):
        """Test handling of generic exceptions."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler to raise generic exception
        mock_provider_handler = MagicMock()
        mock_provider_handler.verify_repo_provider = AsyncMock(
            side_effect=Exception('Unexpected error')
        )

        with patch(
            'openhands.server.routes.git.ProviderHandler',
            return_value=mock_provider_handler,
        ):
            response = test_client.get('/api/user/repository/test/repo/microagents')

            assert response.status_code == 500
            assert 'Error scanning repository' in response.json()

    @pytest.mark.asyncio
    async def test_get_microagents_timeout(self, test_client, mock_provider_tokens):
        """Test timeout handling during git clone."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run to raise timeout
        import subprocess

        with patch(
            'openhands.server.routes.git.ProviderHandler',
            return_value=mock_provider_handler,
        ):
            with patch(
                'openhands.server.routes.git.subprocess.run',
                side_effect=subprocess.TimeoutExpired('git', 30),
            ):
                response = test_client.get('/api/user/repository/test/repo/microagents')

                assert response.status_code == 500
                assert 'Error scanning repository' in response.json()

    @pytest.mark.asyncio
    async def test_get_microagents_microagents_without_mcp_tools(
        self, test_client, mock_provider_tokens
    ):
        """Test microagents without MCP tools."""
        # Override the dependency to use mock provider tokens
        test_client.app.dependency_overrides[get_provider_tokens] = (
            lambda: mock_provider_tokens
        )

        # Create microagent without MCP tools
        repo_microagent = RepoMicroagent(
            name='simple_agent',
            content='Simple agent without MCP tools',
            metadata=MicroagentMetadata(
                name='simple_agent',
                type=MicroagentType.REPO_KNOWLEDGE,
                inputs=[],
                mcp_tools=None,
            ),
            source='test_source',
            type=MicroagentType.REPO_KNOWLEDGE,
        )

        # Mock ProviderHandler
        mock_provider_handler = MagicMock()
        mock_repository = Repository(
            id='123456',
            full_name='test/repo',
            git_provider=ProviderType.GITHUB,
            is_public=True,
            stargazers_count=100,
        )
        mock_provider_handler.verify_repo_provider = AsyncMock(
            return_value=mock_repository
        )

        # Mock subprocess.run for successful clone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ''

        # Create temporary directory with microagents
        temp_dir = tempfile.mkdtemp()
        microagents_dir = Path(temp_dir) / 'repo' / '.openhands' / 'microagents'
        microagents_dir.mkdir(parents=True, exist_ok=True)

        # Mock load_microagents_from_dir
        mock_repo_agents = {'simple_agent': repo_microagent}
        mock_knowledge_agents = {}

        try:
            with patch(
                'openhands.server.routes.git.ProviderHandler',
                return_value=mock_provider_handler,
            ):
                with patch(
                    'openhands.server.routes.git.subprocess.run',
                    return_value=mock_result,
                ):
                    with patch(
                        'openhands.server.routes.git.load_microagents_from_dir',
                        return_value=(
                            mock_repo_agents,
                            mock_knowledge_agents,
                        ),
                    ):
                        with patch(
                            'openhands.server.routes.git.tempfile.mkdtemp',
                            return_value=temp_dir,
                        ):
                            with patch(
                                'openhands.server.routes.git._get_file_creation_time',
                                return_value=datetime.now(),
                            ):
                                response = test_client.get(
                                    '/api/user/repository/test/repo/microagents'
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert len(data) == 1
                                assert data[0]['name'] == 'simple_agent'
                                assert data[0]['tools'] == []
                                assert 'created_at' in data[0]
                                assert 'git_provider' in data[0]
                                assert data[0]['git_provider'] == 'github'
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
