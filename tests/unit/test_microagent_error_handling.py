"""Tests for microagent error handling and logging behavior."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import OpenHandsConfig, SandboxConfig
from openhands.events import EventStream
from openhands.integrations.service_types import AuthenticationError
from openhands.runtime.base import Runtime


class MockRuntime(Runtime):
    """Mock runtime for testing error handling."""

    def __init__(self, workspace_root: Path):
        # Create a minimal config for testing
        config = OpenHandsConfig()
        config.workspace_mount_path_in_sandbox = str(workspace_root)
        config.sandbox = SandboxConfig()

        # Create a mock event stream
        event_stream = MagicMock(spec=EventStream)

        # Initialize the parent class properly
        super().__init__(
            config=config, event_stream=event_stream, sid='test', git_provider_tokens={}
        )

        self._workspace_root = workspace_root
        self._logs = []

    @property
    def workspace_root(self) -> Path:
        """Return the workspace root path."""
        return self._workspace_root

    def log(self, level: str, message: str):
        """Mock log method that captures logs."""
        self._logs.append((level, message))

    def get_logs(self):
        """Return captured logs."""
        return self._logs

    def run_action(self, action):
        """Mock run_action method."""
        from openhands.events.observation import CmdOutputObservation

        return CmdOutputObservation(content='', exit_code=0)

    def read(self, action):
        """Mock read method."""
        from openhands.events.observation import ErrorObservation

        return ErrorObservation('File not found')

    def _load_microagents_from_directory(self, directory: Path, source: str):
        """Mock microagent loading."""
        return []

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
        return []

    def get_mcp_config(self, extra_stdio_servers=None):
        from openhands.core.config.mcp_config import MCPConfig

        return MCPConfig()

    def call_tool_mcp(self, action):
        from openhands.events.observation import MCPObservation

        return MCPObservation(content='', tool='', result='')


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_get_microagents_from_org_or_user_authentication_error_logging(temp_workspace):
    """Test that AuthenticationError is logged at debug level, not error level."""
    runtime = MockRuntime(temp_workspace)

    # Mock the provider detection to return GitHub
    with patch.object(runtime, '_is_gitlab_repository', return_value=False):
        # Mock the get_authenticated_git_url to raise AuthenticationError
        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            mock_async.side_effect = AuthenticationError('Repository not found')

            result = runtime.get_microagents_from_org_or_user('github.com/owner/repo')

            # Should return empty list
            assert len(result) == 0

            # Check logs - should have debug message, not error message
            logs = runtime.get_logs()
            debug_logs = [log for log in logs if log[0] == 'debug']
            error_logs = [log for log in logs if log[0] == 'error']

            # Should have debug message about org-level microagent directory not found
            assert any('org-level microagent directory' in log[1] for log in debug_logs)
            # Should not have error logs for this case
            assert len(error_logs) == 0


def test_get_microagents_from_org_or_user_generic_exception_logging(temp_workspace):
    """Test that generic exceptions are still logged at debug level."""
    runtime = MockRuntime(temp_workspace)

    # Mock the provider detection to return GitHub
    with patch.object(runtime, '_is_gitlab_repository', return_value=False):
        # Mock the get_authenticated_git_url to raise a generic exception
        with patch('openhands.runtime.base.call_async_from_sync') as mock_async:
            mock_async.side_effect = ValueError('Some other error')

            result = runtime.get_microagents_from_org_or_user('github.com/owner/repo')

            # Should return empty list
            assert len(result) == 0

            # Check logs - should have debug message, not error message
            logs = runtime.get_logs()
            debug_logs = [log for log in logs if log[0] == 'debug']
            error_logs = [log for log in logs if log[0] == 'error']

            # Should have debug message about error loading org-level microagents
            assert any(
                'Error loading org-level microagents' in log[1] for log in debug_logs
            )
            # Should not have error logs for this case
            assert len(error_logs) == 0


def test_get_microagents_from_org_or_user_insufficient_repo_parts(temp_workspace):
    """Test that insufficient repository parts are handled correctly."""
    runtime = MockRuntime(temp_workspace)

    result = runtime.get_microagents_from_org_or_user('invalid-repo')

    # Should return empty list
    assert len(result) == 0

    # Check logs - should have warning about insufficient parts
    logs = runtime.get_logs()
    warning_logs = [log for log in logs if log[0] == 'warning']

    assert any('insufficient parts' in log[1] for log in warning_logs)
