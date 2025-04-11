from types import MappingProxyType

import pytest
from pydantic import SecretStr

from openhands.core.config import AppConfig
from openhands.events.action import Action
from openhands.events.action.commands import CmdRunAction
from openhands.events.observation import NullObservation, Observation
from openhands.events.stream import EventStream
from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


class TestRuntime(Runtime):
    """A concrete implementation of Runtime for testing"""

    async def connect(self):
        pass

    def close(self):
        pass

    def browse(self, action):
        return NullObservation()

    def browse_interactive(self, action):
        return NullObservation()

    def run(self, action):
        return NullObservation()

    def run_ipython(self, action):
        return NullObservation()

    def read(self, action):
        return NullObservation()

    def write(self, action):
        return NullObservation()

    def copy_from(self, path):
        return ''

    def copy_to(self, path, content):
        pass

    def list_files(self, path):
        return []

    def run_action(self, action: Action) -> Observation:
        return NullObservation()

    def call_tool_mcp(self, action):
        return NullObservation()


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
