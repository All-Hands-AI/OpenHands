import pathlib
import tempfile
from unittest.mock import MagicMock, call, patch

import pytest

from opendevin.core.config import AppConfig, SandboxConfig
from opendevin.events.action import IPythonRunCellAction
from opendevin.events.observation import IPythonRunCellObservation
from opendevin.runtime.server.runtime import ServerRuntime


@pytest.fixture
def temp_dir(monkeypatch):
    # get a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        pathlib.Path().mkdir(parents=True, exist_ok=True)
        yield temp_dir


@pytest.mark.asyncio
async def test_run_python_backticks():
    # Create a mock event_stream
    mock_event_stream = MagicMock()

    test_code = "print('Hello, `World`!\n')"

    # Mock the asynchronous sandbox execute method
    mock_sandbox_execute = MagicMock()
    mock_sandbox_execute.side_effect = [
        (0, ''),  # Initial call during DockerSSHBox initialization
        (0, ''),  # Initial call during DockerSSHBox initialization
        (0, ''),  # Initial call during DockerSSHBox initialization
        (0, ''),  # Write command
        (0, test_code),  # Execute command
    ]

    # Set up the patches for the runtime and sandbox
    with patch(
        'opendevin.runtime.docker.ssh_box.DockerSSHBox.execute',
        new=mock_sandbox_execute,
    ):
        # Initialize the runtime with the mock event_stream
        runtime = ServerRuntime(
            config=AppConfig(
                persist_sandbox=False, sandbox=SandboxConfig(box_type='ssh')
            ),
            event_stream=mock_event_stream,
        )

        # Define the test action with a simple IPython command
        action = IPythonRunCellAction(code=test_code)

        # Call the run_ipython method with the test action
        result = await runtime.run_action(action)

        # Assert that the result is an instance of IPythonRunCellObservation
        assert isinstance(result, IPythonRunCellObservation)

        # Assert that the execute method was called with the correct commands
        expected_write_command = (
            "cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n" f'{test_code}\n' 'EOL'
        )
        expected_execute_command = 'cat /tmp/opendevin_jupyter_temp.py | execute_cli'
        mock_sandbox_execute.assert_has_calls(
            [
                call('mkdir -p /tmp'),
                call('git config --global user.name "OpenDevin"'),
                call('git config --global user.email "opendevin@all-hands.dev"'),
                call(expected_write_command),
                call(expected_execute_command),
            ]
        )

        assert (
            test_code == result.content
        ), f'The output should contain the expected print output, got: {result.content}'
