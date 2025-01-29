import os
import pytest
from unittest.mock import MagicMock
from openhands.core.config import AppConfig
from openhands.events import EventStream
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime


class MockRuntime(Runtime):
    """Mock runtime class for testing."""
    def browse(self, action):
        pass

    def browse_interactive(self, action):
        pass

    async def connect(self):
        pass

    def copy_from(self, path):
        pass

    def copy_to(self, host_src, sandbox_dest, recursive=False):
        pass

    def list_files(self, path=None):
        pass

    def read(self, action):
        pass

    def run(self, action):
        pass

    def run_ipython(self, action):
        pass

    def write(self, action):
        pass


@pytest.fixture
def app_config():
    return AppConfig()


@pytest.fixture
def event_stream():
    from openhands.storage import InMemoryFileStore
    return EventStream("test", InMemoryFileStore())


def test_env_vars_persist(app_config, event_stream):
    # Create a mock runtime instance
    runtime = MockRuntime(app_config, event_stream)
    runtime.run = MagicMock()

    # Add a test environment variable
    test_env = {"TEST_VAR": "test_value"}

    # Mock the run method to simulate successful command execution
    def mock_run(action):
        print(f"Actual command: {action.command}")
        if all(part in action.command for part in ['grep -q "^export TEST_VAR="', '~/.bashrc', 'echo "export TEST_VAR=']):
            return CmdOutputObservation(command=action.command, content="", exit_code=0)
        elif 'export TEST_VAR=' in action.command:
            return CmdOutputObservation(command=action.command, content="", exit_code=0)
        return CmdOutputObservation(command=action.command, content=f"Command not matched: {action.command}", exit_code=1)

    runtime.run.side_effect = mock_run

    # Add the environment variable
    runtime.add_env_vars(test_env)

    # Verify that both commands were called
    assert runtime.run.call_count == 2

    # Verify the commands that were called
    calls = runtime.run.call_args_list
    assert any('export TEST_VAR=' in call[0][0].command for call in calls)
    assert any(all(part in call[0][0].command for part in ['grep -q "^export TEST_VAR="', '~/.bashrc', 'echo "export TEST_VAR=']) for call in calls)
