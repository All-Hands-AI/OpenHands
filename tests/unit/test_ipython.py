import pathlib
import tempfile
from unittest.mock import MagicMock, call, patch

import pytest

from opendevin.core.config import config
from opendevin.events.action import IPythonRunCellAction
from opendevin.events.observation import IPythonRunCellObservation
from opendevin.runtime.docker.ssh_box import DockerSSHBox
from opendevin.runtime.plugins import JupyterRequirement
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
        runtime = ServerRuntime(event_stream=mock_event_stream)

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
                call('git config --global user.email "opendevin@opendevin.ai"'),
                call(expected_write_command),
                call(expected_execute_command),
            ]
        )

        assert (
            test_code == result.content
        ), f'The output should contain the expected print output, got: {result.content}'


def test_sandbox_jupyter_plugin_backticks(temp_dir):
    # get a temporary directory
    with patch.object(config, 'workspace_base', new=temp_dir), patch.object(
        config, 'workspace_mount_path', new=temp_dir
    ), patch.object(config, 'run_as_devin', new='true'), patch.object(
        config, 'sandbox_type', new='ssh'
    ):
        for box in [DockerSSHBox()]:
            box.init_plugins([JupyterRequirement])
            test_code = "print('Hello, `World`!')"
            expected_write_command = (
                "cat > /tmp/opendevin_jupyter_temp.py <<'EOL'\n" f'{test_code}\n' 'EOL'
            )
            expected_execute_command = (
                'cat /tmp/opendevin_jupyter_temp.py | execute_cli'
            )
            exit_code, output = box.execute(expected_write_command)
            exit_code, output = box.execute(expected_execute_command)
            print(output)
            assert exit_code == 0, (
                'The exit code should be 0 for ' + box.__class__.__name__
            )
            assert output.strip() == 'Hello, `World`!', (
                'The output should be the same as the input for '
                + box.__class__.__name__
            )
            box.close()
