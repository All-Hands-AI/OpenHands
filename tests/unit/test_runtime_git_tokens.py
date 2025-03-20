import pytest
from types import MappingProxyType
from pydantic import SecretStr

from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.events.action.commands import CmdRunAction
from openhands.events.action import Action
from openhands.events.observation import Observation, NullObservation
from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.runtime.base import Runtime


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
        return ""

    def copy_to(self, path, content):
        pass

    def list_files(self, path):
        return []

    def run_action(self, action: Action) -> Observation:
        return NullObservation()


@pytest.fixture
def event_stream():
    """Fixture for event stream testing"""
    class TestEventStream:
        def __init__(self):
            self.secrets = {}

        def set_secrets(self, secrets):
            self.secrets = secrets

        def add_event(self, event, source):
            pass

        def subscribe(self, subscriber, callback, sid):
            pass

    return TestEventStream()


@pytest.fixture
def runtime(event_stream):
    """Fixture for runtime testing"""
    config = AppConfig()
    git_provider_tokens = MappingProxyType({
        ProviderType.GITHUB: ProviderToken(token=SecretStr('test_token'))
    })
    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens
    )
    return runtime


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_no_user_id(event_stream):
    """Test that no token export happens when user_id is not set"""
    config = AppConfig()
    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test'
    )

    # Create a command that would normally trigger token export
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')
    
    # This should not raise any errors and should return None
    await runtime._export_latest_git_provider_tokens(cmd)
    
    # Verify no secrets were set
    assert not event_stream.secrets


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_no_token_ref(event_stream):
    """Test that no token export happens when command doesn't reference tokens"""
    config = AppConfig()
    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user'
    )

    # Create a command that doesn't reference any tokens
    cmd = CmdRunAction(command='echo "hello"')
    
    # This should not raise any errors and should return None
    await runtime._export_latest_git_provider_tokens(cmd)
    
    # Verify no secrets were set
    assert not event_stream.secrets


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_success(runtime, event_stream):
    """Test successful token export when command references tokens"""
    # Create a command that references the GitHub token
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')
    
    # Export the tokens
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify that the token was exported to the event stream
    assert event_stream.secrets == {'github_token': 'test_token'}

    # Verify that the token was added to environment variables
    # This is done by checking if the command to add the env var was executed
    # We can't directly check the env vars as they're in the runtime environment
    assert runtime.prev_token is not None
    assert runtime.prev_token.get_secret_value() == 'test_token'


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_multiple_refs(event_stream):
    """Test token export with multiple token references"""
    config = AppConfig()
    # Initialize with both GitHub and GitLab tokens
    git_provider_tokens = MappingProxyType({
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github_token')),
        ProviderType.GITLAB: ProviderToken(token=SecretStr('gitlab_token'))
    })
    runtime = TestRuntime(
        config=config,
        event_stream=event_stream,
        sid='test',
        user_id='test_user',
        git_provider_tokens=git_provider_tokens
    )

    # Create a command that references multiple tokens
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN && echo $GITLAB_TOKEN')
    
    # Export the tokens
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify that both tokens were exported
    assert event_stream.secrets == {
        'github_token': 'github_token',
        'gitlab_token': 'gitlab_token'
    }
    # The prev_token should store the GitHub token
    assert runtime.prev_token is not None
    assert runtime.prev_token.get_secret_value() == 'github_token'


@pytest.mark.asyncio
async def test_export_latest_git_provider_tokens_token_update(runtime, event_stream):
    """Test that token updates are handled correctly"""
    # First export with initial token
    cmd = CmdRunAction(command='echo $GITHUB_TOKEN')
    await runtime._export_latest_git_provider_tokens(cmd)
    
    # Update the token
    new_token = 'new_test_token'
    runtime.provider_handler._provider_tokens = MappingProxyType({
        ProviderType.GITHUB: ProviderToken(token=SecretStr(new_token))
    })
    
    # Export again with updated token
    await runtime._export_latest_git_provider_tokens(cmd)

    # Verify that the new token was exported
    assert event_stream.secrets == {'github_token': new_token}
    assert runtime.prev_token is not None
    assert runtime.prev_token.get_secret_value() == new_token