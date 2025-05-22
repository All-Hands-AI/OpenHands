from types import MappingProxyType
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from openhands.core.config import AppConfig
from openhands.events.action import Action
from openhands.events.action.commands import CmdRunAction
from openhands.events.observation import NullObservation, Observation
from openhands.events.stream import EventStream
from openhands.integrations.provider import ProviderHandler, ProviderToken, ProviderType
from openhands.integrations.service_types import AuthenticationError, Repository
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


class TestRuntime(Runtime):
    """A concrete implementation of Runtime for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_action_calls = []
        self._execute_shell_fn_git_handler = MagicMock(
            return_value=MagicMock(exit_code=0, stdout='', stderr='')
        )

    async def connect(self):
        pass

    def close(self):
        pass

    def browse(self, action):
        return NullObservation(content='')

    def browse_interactive(self, action):
        return NullObservation(content='')

    def run(self, action):
        return NullObservation(content='')

    def run_ipython(self, action):
        return NullObservation(content='')

    def read(self, action):
        return NullObservation(content='')

    def write(self, action):
        return NullObservation(content='')

    def copy_from(self, path):
        return ''

    def copy_to(self, path, content):
        pass

    def list_files(self, path):
        return []

    def run_action(self, action: Action) -> Observation:
        self.run_action_calls.append(action)
        return NullObservation(content='')

    def call_tool_mcp(self, action):
        return NullObservation(content='')


@pytest.fixture
def temp_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('test_event_stream'))


@pytest.fixture
def runtime(temp_dir):
    """Fixture for runtime testing"""
    config = AppConfig()
    git_provider_tokens = MappingProxyType(
        {ProviderType.GITHUB: ProviderToken(token=SecretStr('test_token'))}
    )
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens,
    )
    return runtime


def mock_repo_and_patch(monkeypatch, provider=ProviderType.GITHUB, is_public=True):
    repo = Repository(
        id=123, full_name='owner/repo', git_provider=provider, is_public=is_public
    )

    async def mock_verify_repo_provider(*_args, **_kwargs):
        return repo

    monkeypatch.setattr(
        ProviderHandler, 'verify_repo_provider', mock_verify_repo_provider
    )
    return repo


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_no_user_id(temp_dir):
    """Test that no token export happens when user_id is not set"""
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(config=config, event_stream=event_stream, sid='test')

    # Create a command that would normally trigger token export
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')

    # This should not raise any errors and should return None
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify no secrets were set
    assert not event_stream.secrets


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_no_token_ref(temp_dir):
    """Test that no token export happens when command doesn't reference tokens"""
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id='test_user'
    )

    # Create a command that doesn't reference any tokens
    cmd = CmdRunAction(command='echo "hello"')

    # This should not raise any errors and should return None
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify no secrets were set
    assert not event_stream.secrets


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_success(runtime):
    """Test successful token export when command references tokens"""
    # Create a command that references the GitHub token
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')

    # Export the tokens
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify that the token was exported to the event stream
    assert runtime.event_stream.secrets == {'github_token': 'test_token'}


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_multiple_refs(temp_dir):
    """Test token export with multiple token references"""
    config = AppConfig()
    # Initialize with both GitHub and GitLab tokens
    git_provider_tokens = MappingProxyType(
        {
            ProviderType.GITHUB: ProviderToken(token=SecretStr('github_token')),
            ProviderType.GITLAB: ProviderToken(token=SecretStr('gitlab_token')),
        }
    )
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens,
    )

    # Create a command that references multiple tokens
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN && echo $GITLAB_TOKEN')

    # Export the tokens
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify that both tokens were exported
    assert event_stream.secrets == {
        'github_token': 'github_token',
        'gitlab_token': 'gitlab_token',
    }


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_token_update(runtime):
    """Test that token updates are handled correctly"""
    # First export with initial token
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')
    await runtime._export_latest_git_provider_tokens(cmd)

    # Update the token
    new_token = 'new_test_token'
    runtime.provider_handler._provider_tokens = MappingProxyType(
        {ProviderType.GITHUB: ProviderToken(token=SecretStr(new_token))}
    )

    # Export again with updated token
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify that the new token was exported
    assert runtime.event_stream.secrets == {'github_token': new_token}


@pytest.mark.asyncio
async def test_clone_or_init_repo_no_repo_with_user_id(temp_dir):
    """Test that git init is run when no repository is selected and user_id is set"""
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id='test_user'
    )

    # Call the function with no repository
    result = await runtime.clone_or_init_repo(None, None, None)

    # Verify that git init was called
    assert len(runtime.run_action_calls) == 1
    assert isinstance(runtime.run_action_calls[0], CmdRunAction)
    assert runtime.run_action_calls[0].command == 'git init'
    assert result == ''


@pytest.mark.asyncio
async def test_clone_or_init_repo_no_repo_no_user_id_no_workspace_base(temp_dir):
    """Test that git init is run when no repository is selected, no user_id, and no workspace_base"""
    config = AppConfig()
    config.workspace_base = None  # Ensure workspace_base is not set
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id=None
    )

    # Call the function with no repository
    result = await runtime.clone_or_init_repo(None, None, None)

    # Verify that git init was called
    assert len(runtime.run_action_calls) == 1
    assert isinstance(runtime.run_action_calls[0], CmdRunAction)
    assert runtime.run_action_calls[0].command == 'git init'
    assert result == ''


@pytest.mark.asyncio
async def test_clone_or_init_repo_no_repo_no_user_id_with_workspace_base(temp_dir):
    """Test that git init is not run when no repository is selected, no user_id, but workspace_base is set"""
    config = AppConfig()
    config.workspace_base = '/some/path'  # Set workspace_base
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id=None
    )

    # Call the function with no repository
    result = await runtime.clone_or_init_repo(None, None, None)

    # Verify that git init was not called
    assert len(runtime.run_action_calls) == 0
    assert result == ''


@pytest.mark.asyncio
async def test_clone_or_init_repo_auth_error(temp_dir):
    """Test that RuntimeError is raised when authentication fails"""
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)
    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id='test_user'
    )

    # Mock the verify_repo_provider method to raise AuthenticationError
    with patch.object(
        ProviderHandler,
        'verify_repo_provider',
        side_effect=AuthenticationError('Auth failed'),
    ):
        # Call the function with a repository
        with pytest.raises(RuntimeError) as excinfo:
            await runtime.clone_or_init_repo(None, 'owner/repo', None)

        # Verify the error message
        assert 'Git provider authentication issue when cloning repo' in str(
            excinfo.value
        )


@pytest.mark.asyncio
async def test_clone_or_init_repo_github_with_token(temp_dir, monkeypatch):
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    github_token = 'github_test_token'
    git_provider_tokens = MappingProxyType(
        {ProviderType.GITHUB: ProviderToken(token=SecretStr(github_token))}
    )

    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens,
    )

    mock_repo_and_patch(monkeypatch, provider=ProviderType.GITHUB)

    result = await runtime.clone_or_init_repo(git_provider_tokens, 'owner/repo', None)

    cmd = runtime.run_action_calls[0].command
    assert f'git clone https://{github_token}@github.com/owner/repo.git repo' in cmd
    assert result == 'repo'


@pytest.mark.asyncio
async def test_clone_or_init_repo_github_no_token(temp_dir, monkeypatch):
    """Test cloning a GitHub repository without a token"""
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id='test_user'
    )

    mock_repo_and_patch(monkeypatch, provider=ProviderType.GITHUB)
    result = await runtime.clone_or_init_repo(None, 'owner/repo', None)

    # Verify that git clone was called with the public URL
    assert len(runtime.run_action_calls) == 1
    assert isinstance(runtime.run_action_calls[0], CmdRunAction)

    # Check that the command contains the correct URL format without token
    cmd = runtime.run_action_calls[0].command
    assert 'git clone https://github.com/owner/repo.git repo' in cmd
    assert 'cd repo' in cmd
    assert 'git checkout -b openhands-workspace-' in cmd
    assert result == 'repo'


@pytest.mark.asyncio
async def test_clone_or_init_repo_gitlab_with_token(temp_dir, monkeypatch):
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    gitlab_token = 'gitlab_test_token'
    git_provider_tokens = MappingProxyType(
        {ProviderType.GITLAB: ProviderToken(token=SecretStr(gitlab_token))}
    )

    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens,
    )

    mock_repo_and_patch(monkeypatch, provider=ProviderType.GITLAB)

    result = await runtime.clone_or_init_repo(git_provider_tokens, 'owner/repo', None)

    cmd = runtime.run_action_calls[0].command
    assert (
        f'git clone https://oauth2:{gitlab_token}@gitlab.com/owner/repo.git repo' in cmd
    )
    assert result == 'repo'


@pytest.mark.asyncio
async def test_clone_or_init_repo_with_branch(temp_dir, monkeypatch):
    """Test cloning a repository with a specified branch"""
    config = AppConfig()
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    runtime = TestRuntime(
        config=config, event_stream=event_stream, sid='test', user_id='test_user'
    )

    mock_repo_and_patch(monkeypatch, provider=ProviderType.GITHUB)
    result = await runtime.clone_or_init_repo(None, 'owner/repo', 'feature-branch')

    # Verify that git clone was called with the correct branch checkout
    assert len(runtime.run_action_calls) == 1
    assert isinstance(runtime.run_action_calls[0], CmdRunAction)

    # Check that the command contains the correct branch checkout
    cmd = runtime.run_action_calls[0].command
    assert 'git clone https://github.com/owner/repo.git repo' in cmd
    assert 'cd repo' in cmd
    assert 'git checkout feature-branch' in cmd
    assert 'git checkout -b' not in cmd  # Should not create a new branch
    assert result == 'repo'
