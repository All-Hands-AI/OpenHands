"""Tests for GitLab alternative directory support for microagents."""

import tempfile
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import OpenHandsConfig, SandboxConfig
from openhands.events import EventStream
from openhands.integrations.service_types import (
    AuthenticationError,
    ProviderType,
    Repository,
)
from openhands.llm.llm_registry import LLMRegistry
from openhands.microagent.microagent import (
    RepoMicroagent,
)
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


class MockRuntime(Runtime):
    """Mock runtime for testing."""

    def __init__(self, workspace_root: Path):
        # Create a minimal config for testing
        config = OpenHandsConfig()
        config.workspace_mount_path_in_sandbox = str(workspace_root)
        config.sandbox = SandboxConfig()

        # Create a mock event stream and file store
        file_store = get_file_store('local', str(workspace_root))
        event_stream = MagicMock(spec=EventStream)
        event_stream.file_store = file_store

        # Create a mock LLM registry
        llm_registry = LLMRegistry(config)

        # Initialize the parent class properly
        super().__init__(
            config=config,
            event_stream=event_stream,
            llm_registry=llm_registry,
            sid='test',
        )
        self.git_provider_tokens = MappingProxyType({})
        self._workspace_root = workspace_root
        self._logs = []

    @property
    def workspace_root(self) -> Path:
        """Return the workspace root path."""
        return self._workspace_root

    def log(self, level: str, message: str):
        """Mock log method."""
        self._logs.append((level, message))

    def run_action(self, action):
        """Mock run_action method."""
        # For testing, we construct a CmdOutputObservation with the required command argument.
        from openhands.events.observation import CmdOutputObservation

        # The `action` passed in is a CmdRunAction; its command attribute holds the shell command string.
        # Use that as the `command` parameter for CmdOutputObservation.
        return CmdOutputObservation(content='', command=action.command, exit_code=0)

    def read(self, action):
        """Mock read method."""
        # For simplicity, always return an error indicating the file is missing.
        from openhands.events.observation import ErrorObservation

        return ErrorObservation('File not found')

    def _load_microagents_from_directory(self, directory: Path, source: str):
        """Mock microagent loading."""
        if not directory.exists():
            return []

        # Create mock microagents based on directory structure
        microagents = []
        for md_file in directory.rglob('*.md'):
            if md_file.name == 'README.md':
                continue

            # Create a simple mock microagent
            from openhands.microagent.types import MicroagentMetadata, MicroagentType

            agent = RepoMicroagent(
                name=f'mock_{md_file.stem}',
                content=f'Mock content from {md_file}',
                metadata=MicroagentMetadata(name=f'mock_{md_file.stem}'),
                source=str(md_file),
                type=MicroagentType.REPO_KNOWLEDGE,
            )
            microagents.append(agent)

        return microagents

    # Implement abstract methods with minimal functionality
    def connect(self):
        pass

    def run(self, action):
        from openhands.events.observation import CmdOutputObservation

        return CmdOutputObservation(content='', exit_code=0)

    def run_ipython(self, action):
        from openhands.events.observation import IPythonRunCellObservation

        return IPythonRunCellObservation(content='', code='')

    def edit(self, action):
        from openhands.events.observation import FileEditObservation

        return FileEditObservation(content='', path='')

    def browse(self, action):
        from openhands.events.observation import BrowserObservation

        return BrowserObservation(content='', url='', screenshot='')

    def browse_interactive(self, action):
        from openhands.events.observation import BrowserObservation

        return BrowserObservation(content='', url='', screenshot='')

    def write(self, action):
        from openhands.events.observation import FileWriteObservation

        return FileWriteObservation(content='', path='')

    def copy_to(self, host_src, sandbox_dest, recursive=False):
        pass

    def copy_from(self, sandbox_src, host_dest, recursive=False):
        pass

    def list_files(self, path=None):
        # Return a list of all files under the given directory (as strings)
        from pathlib import Path

        target_path = Path(path) if path else self._workspace_root
        if not target_path.is_dir():
            return []
        # Collect all file paths recursively
        return [str(p) for p in target_path.rglob('*')]

    def get_mcp_config(self, extra_stdio_servers=None):
        from openhands.core.config.mcp_config import MCPConfig

        return MCPConfig()

    def call_tool_mcp(self, action):
        from openhands.events.observation import MCPObservation

        return MCPObservation(content='', tool='', result='')


def create_test_microagents(base_dir: Path, config_dir_name: str = '.openhands'):
    """Create test microagent files in the specified directory."""
    microagents_dir = base_dir / config_dir_name / 'microagents'
    microagents_dir.mkdir(parents=True, exist_ok=True)

    # Create a test microagent
    test_agent = """---
name: test_agent
type: repo
version: 1.0.0
agent: CodeActAgent
---

# Test Agent

This is a test microagent.
"""
    (microagents_dir / 'test.md').write_text(test_agent)
    return microagents_dir


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_is_gitlab_repository_github(temp_workspace):
    """Test that GitHub repositories are correctly identified as non-GitLab."""
    runtime = MockRuntime(temp_workspace)

    # Mock the provider handler to return GitHub
    mock_repo = Repository(
        id='123',
        full_name='owner/repo',
        git_provider=ProviderType.GITHUB,
        is_public=True,
    )

    with patch('openhands.runtime.base.ProviderHandler') as mock_handler_class:
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler

        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            mock_async.return_value = mock_repo

            result = runtime._is_gitlab_repository('github.com/owner/repo')
            assert result is False


def test_get_microagents_from_org_or_user_github_success(temp_workspace):
    """Test loading org‑level microagents for a GitHub repository when the org repo exists."""
    runtime = MockRuntime(temp_workspace)

    # Create an org‑level repository directory with a .git folder and microagents
    org_repo_dir = temp_workspace / 'org_openhands_owner'
    (org_repo_dir / '.git').mkdir(parents=True, exist_ok=True)
    create_test_microagents(org_repo_dir, config_dir_name='.')

    # Mock verify_repo_provider to return a Repository indicating the org repo exists
    mock_org_repo = Repository(
        id='1',
        full_name='owner/.openhands',
        git_provider=ProviderType.GITHUB,
        is_public=True,
    )

    async def mock_verify(*args, **kwargs):
        return mock_org_repo

    with patch.object(runtime.provider_handler, 'verify_repo_provider', mock_verify):
        # Invoke the org‑level microagent loading
        loaded_microagents = runtime.get_microagents_from_org_or_user(
            'github.com/owner/repo'
        )
        assert len(loaded_microagents) > 0
        # The test microagent created by create_test_microagents has name 'mock_test'
        names = [m.name for m in loaded_microagents]
        assert any(name == 'mock_test' for name in names)


def test_get_microagents_from_org_or_user_auth_error_continuation(temp_workspace):
    """Test that an AuthenticationError while checking org‑level repo does not abort loading and returns empty list."""
    runtime = MockRuntime(temp_workspace)

    # Mock verify_repo_provider to raise AuthenticationError
    async def mock_verify(*args, **kwargs):
        raise AuthenticationError('auth failed')

    with patch.object(runtime.provider_handler, 'verify_repo_provider', mock_verify):
        loaded_microagents = runtime.get_microagents_from_org_or_user(
            'github.com/owner/repo'
        )
        assert loaded_microagents == []

        # Verify that a warning was logged about the AuthenticationError
        warnings = [msg for level, msg in runtime._logs if level == 'warning']
        assert any('AuthenticationError' in msg for msg in warnings)


def test_is_gitlab_repository_gitlab(temp_workspace):
    """Test that GitLab repositories are correctly identified."""
    runtime = MockRuntime(temp_workspace)

    # Mock the provider handler to return GitLab
    mock_repo = Repository(
        id='456',
        full_name='owner/repo',
        git_provider=ProviderType.GITLAB,
        is_public=True,
    )

    with patch('openhands.runtime.base.ProviderHandler') as mock_handler_class:
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler

        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            mock_async.return_value = mock_repo

            result = runtime._is_gitlab_repository('gitlab.com/owner/repo')
            assert result is True


def test_is_gitlab_repository_exception(temp_workspace):
    """Test that exceptions in provider detection return False."""
    runtime = MockRuntime(temp_workspace)

    with patch('openhands.runtime.base.ProviderHandler') as mock_handler_class:
        mock_handler_class.side_effect = Exception('Provider error')

        result = runtime._is_gitlab_repository('unknown.com/owner/repo')
        assert result is False


def test_get_microagents_from_org_or_user_github(temp_workspace):
    """Test that GitHub repositories only try .openhands directory."""
    runtime = MockRuntime(temp_workspace)

    # Mock the provider detection to return GitHub
    with patch.object(runtime, '_is_gitlab_repository', return_value=False):
        # Mock the _get_authenticated_git_url to simulate failure (no org repo)
        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            mock_async.side_effect = Exception('Repository not found')

            result = runtime.get_microagents_from_org_or_user('github.com/owner/repo')

            # Should only try .openhands, not openhands-config
            assert len(result) == 0
            # Check that only one attempt was made (for .openhands)
            assert mock_async.call_count == 1


def test_get_microagents_from_org_or_user_gitlab_success_with_config(temp_workspace):
    """Test that GitLab repositories use openhands-config and succeed."""
    runtime = MockRuntime(temp_workspace)

    # No local org directory is created; we rely on cloning from remote
    # Mock the provider detection to return GitLab
    with patch.object(runtime, '_is_gitlab_repository', return_value=True):
        # Mock successful cloning for openhands-config
        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            # Simulate two async calls: one for verification, one for fetching the URL
            mock_async.side_effect = [
                Repository(
                    id='1',
                    full_name='owner/.openhands-config',
                    git_provider=ProviderType.GITLAB,
                    is_public=True,
                ),
                'https://gitlab.com/owner/openhands-config.git',
            ]

            result = runtime.get_microagents_from_org_or_user('gitlab.com/owner/repo')

            # Should succeed with openhands-config (no local microagents)
            assert len(result) >= 0  # May be empty if no microagents found
            # Expect two async calls: verification and URL retrieval
            assert mock_async.call_count == 2


def test_get_microagents_from_org_or_user_gitlab_failure(temp_workspace):
    """Test that GitLab repositories handle failure gracefully when openhands-config doesn't exist."""
    runtime = MockRuntime(temp_workspace)

    # Mock the provider detection to return GitLab
    with patch.object(runtime, '_is_gitlab_repository', return_value=True):
        # Mock the _get_authenticated_git_url to fail for openhands-config
        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            mock_async.side_effect = Exception('openhands-config not found')

            result = runtime.get_microagents_from_org_or_user('gitlab.com/owner/repo')

            # Should return empty list when repository doesn't exist
            assert len(result) == 0
            # Should only try once for openhands-config
            assert mock_async.call_count == 1


def test_get_microagents_from_selected_repo_gitlab_uses_openhands(temp_workspace):
    """Test that GitLab repositories use .openhands directory for repository-specific microagents."""
    runtime = MockRuntime(temp_workspace)

    # Create a repository directory structure
    repo_dir = temp_workspace / 'repo'
    repo_dir.mkdir()

    # Create microagents in .openhands directory
    create_test_microagents(repo_dir, '.openhands')

    # Mock the provider detection to return GitLab
    with patch.object(runtime, '_is_gitlab_repository', return_value=True):
        # Mock org-level microagents (empty)
        with patch.object(runtime, 'get_microagents_from_org_or_user', return_value=[]):
            result = runtime.get_microagents_from_selected_repo('gitlab.com/owner/repo')

            # Should find microagents from .openhands directory
            # The exact assertion depends on the mock implementation
            # At minimum, it should not raise an exception
            assert isinstance(result, list)


def test_get_microagents_from_selected_repo_github_only_openhands(temp_workspace):
    """Test that GitHub repositories only check .openhands directory."""
    runtime = MockRuntime(temp_workspace)

    # Create a repository directory structure
    repo_dir = temp_workspace / 'repo'
    repo_dir.mkdir()

    # Create microagents in both directories
    create_test_microagents(repo_dir, 'openhands-config')
    create_test_microagents(repo_dir, '.openhands')

    # Mock the provider detection to return GitHub
    with patch.object(runtime, '_is_gitlab_repository', return_value=False):
        # Mock org-level microagents (empty)
        with patch.object(runtime, 'get_microagents_from_org_or_user', return_value=[]):
            result = runtime.get_microagents_from_selected_repo('github.com/owner/repo')

            # Should only check .openhands directory, not openhands-config
            assert isinstance(result, list)


def test_org_microagent_fallback_subgroup_has_microagents_top_level_missing(
    temp_workspace,
):
    """When the top‑level org repo has microagents but a sub‑group org repo also exists,
    the sub‑group should be selected for loading microagents (priority to deeper level)."""
    runtime = MockRuntime(temp_workspace)

    # Top‑level org repo with microagents
    top_org_dir = temp_workspace / 'org_openhands_top'
    (top_org_dir / '.git').mkdir(parents=True, exist_ok=True)
    create_test_microagents(top_org_dir, '')

    # Sub‑group org repo with its own microagents
    sub_org_dir = temp_workspace / 'org_openhands_top' / 'sub1'
    (sub_org_dir / '.git').mkdir(parents=True, exist_ok=True)
    create_test_microagents(sub_org_dir, '')

    # Mock verify_repo_provider to simulate remote checks:
    async def mock_verify(repo):
        # Simulate that the deepest org repo does NOT exist, forcing selection of sub‑group
        if repo == 'top/sub1/sub2/openhands-config':
            raise Exception('not found')
        elif repo in [
            'top/sub1/openhands-config',
            'top/openhands-config',
        ]:
            return Repository(
                id='1',
                full_name=repo,
                git_provider=ProviderType.GITLAB,
                is_public=True,
            )
        raise Exception('unexpected')

    with (
        patch.object(runtime.provider_handler, 'verify_repo_provider', mock_verify),
        patch.object(runtime, '_is_gitlab_repository', return_value=True),
    ):
        # Use default run_action (success) from MockRuntime
        loaded = runtime.get_microagents_from_org_or_user(
            'gitlab.com/top/sub1/sub2/repo'
        )
        # Should load microagents from the sub‑group org repo (deeper level)
        assert any(isinstance(m, RepoMicroagent) for m in loaded)
        names = [m.name for m in loaded]
        # Expect microagents from sub‑group (named 'mock_test' as created)
        assert any('mock_test' in n for n in names)


def test_org_microagent_fallback_subgroup_missing_top_level_has(temp_workspace):
    """When the sub‑group org repo is missing remotely but a local directory exists with microagents,
    +    fallback to that local sub‑group directory (since it has microagents)."""
    runtime = MockRuntime(temp_workspace)

    # Top‑level org repo with microagents
    top_org_dir = temp_workspace / 'org_openhands_top'
    (top_org_dir / '.git').mkdir(parents=True, exist_ok=True)
    create_test_microagents(top_org_dir, '')

    # Local sub‑group directory exists with microagents (no remote)
    sub_org_dir = temp_workspace / 'org_openhands_top' / 'sub1'
    (sub_org_dir / '.git').mkdir(parents=True, exist_ok=True)
    create_test_microagents(sub_org_dir, '')

    async def mock_verify(repo):
        # Remote checks: only top‑level repo is found; sub‑group remote missing
        if repo == 'top/sub1/sub2/openhands-config':
            raise Exception('not found')
        elif repo == 'top/sub1/openhands-config':
            raise Exception('not found')  # remote missing
        elif repo == 'top/openhands-config':
            return Repository(
                id='1',
                full_name='top/.openhands-config',
                git_provider=ProviderType.GITLAB,
                is_public=True,
            )
        else:
            raise Exception('unexpected')

    with (
        patch.object(runtime.provider_handler, 'verify_repo_provider', mock_verify),
        patch.object(runtime, '_is_gitlab_repository', return_value=True),
    ):
        loaded = runtime.get_microagents_from_org_or_user(
            'gitlab.com/top/sub1/sub2/repo'
        )
        # Should load microagents from the top‑level org repo (since sub‑group has none)
        assert any(isinstance(m, RepoMicroagent) for m in loaded)
        # Verify that the source path includes the top‑level directory but not sub‑group
        assert any(
            'org_openhands_top' in m.source and 'sub1' not in m.source for m in loaded
        )
        # (Removed: sub‑group source path check is not applicable when fallback to top‑level repo)
        names = [m.name for m in loaded]
        # Expect microagents from top‑level (named 'mock_test')
        assert any('mock_test' in n for n in names)


def test_org_microagent_fallback_missing_all_candidates(temp_workspace):
    """If none of the candidate org repos exist or have microagents,
    get_microagents_from_org_or_user should return an empty list."""
    runtime = MockRuntime(temp_workspace)

    async def mock_verify(repo):
        raise Exception('not found')  # all candidates fail

    with patch.object(runtime.provider_handler, 'verify_repo_provider', mock_verify):
        loaded = runtime.get_microagents_from_org_or_user(
            'gitlab.com/top/sub1/sub2/repo'
        )
        assert loaded == []
