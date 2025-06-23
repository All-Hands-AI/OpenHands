"""Unit tests for the setup script fix."""

from unittest.mock import MagicMock

import pytest

from openhands.events.action import CmdRunAction, FileReadAction, FileWriteAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.runtime.base import Runtime


class TestSetupScriptFix:
    """Tests for the setup script fix."""

    @pytest.fixture
    def mock_runtime(self):
        """Create a mock runtime."""
        mock_runtime = MagicMock(spec=Runtime)
        mock_runtime.status_callback = None
        mock_runtime.log = MagicMock()

        # Mock the read method to return a setup script
        def mock_read(action):
            if (
                isinstance(action, FileReadAction)
                and action.path == '.openhands/setup.sh'
            ):
                return FileReadObservation(
                    content="#!/bin/bash\nexport TEST_ENV_VAR='test_value'\necho 'Setup complete!'\n",
                    path='.openhands/setup.sh',
                )
            return ErrorObservation(content=f'File not found: {action.path}')

        mock_runtime.read = MagicMock(side_effect=mock_read)

        # Mock the write method to simulate writing the wrapper script
        mock_runtime.write = MagicMock(
            return_value=FileWriteObservation(content='', path='')
        )

        # Mock the run_action method to simulate running commands
        def mock_run_action(action):
            if isinstance(action, CmdRunAction):
                if 'chmod +x' in action.command:
                    return CmdOutputObservation(
                        content='', exit_code=0, command=action.command
                    )
                elif '/tmp/openhands_setup_wrapper.sh' in action.command:
                    return CmdOutputObservation(
                        content='Setup complete!', exit_code=0, command=action.command
                    )
                elif 'if [ -f /tmp/openhands_setup_env.txt ]' in action.command:
                    return CmdOutputObservation(
                        content='', exit_code=0, command=action.command
                    )
                elif 'echo $TEST_ENV_VAR' in action.command:
                    return CmdOutputObservation(
                        content='test_value', exit_code=0, command=action.command
                    )
            return ErrorObservation(content=f'Unknown action: {action}')

        mock_runtime.run_action = MagicMock(side_effect=mock_run_action)

        return mock_runtime

    def test_maybe_run_setup_script_creates_wrapper(self, mock_runtime):
        """Test that maybe_run_setup_script creates a wrapper script."""
        # Call the method under test
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that the wrapper script was created
        mock_runtime.write.assert_called_once()
        args, kwargs = mock_runtime.write.call_args
        action = args[0]
        assert isinstance(action, FileWriteAction)
        assert action.path == '/tmp/openhands_setup_wrapper.sh'
        assert 'bash -c' in action.content
        assert 'env > /tmp/openhands_setup_env.txt' in action.content

        # Verify that the wrapper script was made executable
        chmod_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction) and 'chmod +x' in call[0][0].command
        ]
        assert len(chmod_calls) > 0

        # Verify that the wrapper script was executed
        wrapper_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction)
            and '/tmp/openhands_setup_wrapper.sh' in call[0][0].command
        ]
        assert len(wrapper_calls) > 0

        # Verify that environment variables were imported
        env_import_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction)
            and 'if [ -f /tmp/openhands_setup_env.txt ]' in call[0][0].command
        ]
        assert len(env_import_calls) > 0

    def test_maybe_run_setup_script_with_complex_script(self, mock_runtime):
        """Test that maybe_run_setup_script handles complex scripts properly."""

        # Mock a complex setup script
        def mock_read(action):
            if (
                isinstance(action, FileReadAction)
                and action.path == '.openhands/setup.sh'
            ):
                return FileReadObservation(
                    content="""#!/bin/bash
set -e

echo "Setting up complex environment..."

# Set environment variables
export COMPLEX_TEST_VAR="complex_value"

# Create a file that indicates the script ran successfully
echo "Setup completed successfully" > setup_completed.txt

# Simulate a long-running process
for i in {1..5}; do
    echo "Processing step $i..."
    sleep 1
done

echo "Setup complete!"
""",
                    path='.openhands/setup.sh',
                )
            return ErrorObservation(content=f'File not found: {action.path}')

        mock_runtime.read = MagicMock(side_effect=mock_read)

        # Call the method under test
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that the wrapper script was created with the correct content
        mock_runtime.write.assert_called_once()
        args, kwargs = mock_runtime.write.call_args
        action = args[0]
        assert isinstance(action, FileWriteAction)
        assert action.path == '/tmp/openhands_setup_wrapper.sh'

        # The wrapper script should run the setup script in a controlled environment
        assert 'bash -c' in action.content
        assert 'source .openhands/setup.sh' in action.content
        assert 'env > /tmp/openhands_setup_env.txt' in action.content

        # Verify that the wrapper script was executed with a timeout
        wrapper_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction)
            and '/tmp/openhands_setup_wrapper.sh' in call[0][0].command
        ]
        assert len(wrapper_calls) > 0

        # The action should have a timeout set
        wrapper_action = wrapper_calls[0][0][0]
        assert hasattr(wrapper_action, 'set_hard_timeout')

        # Verify that environment variables were imported
        env_import_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction)
            and 'if [ -f /tmp/openhands_setup_env.txt ]' in call[0][0].command
        ]
        assert len(env_import_calls) > 0

    def test_maybe_run_setup_script_handles_errors(self, mock_runtime):
        """Test that maybe_run_setup_script handles errors properly."""

        # Mock a failed chmod
        def mock_run_action(action):
            if isinstance(action, CmdRunAction):
                if 'chmod +x /tmp/openhands_setup_wrapper.sh' in action.command:
                    return CmdOutputObservation(
                        content='Permission denied', exit_code=1, command=action.command
                    )
            return CmdOutputObservation(content='', exit_code=0, command=action.command)

        mock_runtime.run_action = MagicMock(side_effect=mock_run_action)

        # Call the method under test
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that an error was logged
        error_logs = [
            call
            for call in mock_runtime.log.call_args_list
            if call[0][0] == 'error'
            and 'Failed to make wrapper script executable' in call[0][1]
        ]
        assert len(error_logs) > 0

        # Reset the mock
        mock_runtime.run_action.reset_mock()
        mock_runtime.log.reset_mock()

        # Mock a failed wrapper script execution
        def mock_run_action_2(action):
            if isinstance(action, CmdRunAction):
                if 'chmod +x' in action.command:
                    return CmdOutputObservation(
                        content='', exit_code=0, command=action.command
                    )
                elif '/tmp/openhands_setup_wrapper.sh' in action.command:
                    return CmdOutputObservation(
                        content='Setup failed', exit_code=1, command=action.command
                    )
            return CmdOutputObservation(content='', exit_code=0, command=action.command)

        mock_runtime.run_action = MagicMock(side_effect=mock_run_action_2)

        # Call the method under test
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that an error was logged
        error_logs = [
            call
            for call in mock_runtime.log.call_args_list
            if call[0][0] == 'error' and 'Setup script failed' in call[0][1]
        ]
        assert len(error_logs) > 0

        # Reset the mock
        mock_runtime.run_action.reset_mock()
        mock_runtime.log.reset_mock()

        # Mock a failed environment variable import
        def mock_run_action_3(action):
            if isinstance(action, CmdRunAction):
                if 'chmod +x' in action.command:
                    return CmdOutputObservation(
                        content='', exit_code=0, command=action.command
                    )
                elif '/tmp/openhands_setup_wrapper.sh' in action.command:
                    return CmdOutputObservation(
                        content='Setup complete!', exit_code=0, command=action.command
                    )
                elif 'if [ -f /tmp/openhands_setup_env.txt ]' in action.command:
                    return CmdOutputObservation(
                        content='Invalid syntax', exit_code=1, command=action.command
                    )
            return CmdOutputObservation(content='', exit_code=0, command=action.command)

        mock_runtime.run_action = MagicMock(side_effect=mock_run_action_3)

        # Call the method under test
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that a warning was logged
        warning_logs = [
            call
            for call in mock_runtime.log.call_args_list
            if call[0][0] == 'warning'
            and 'Failed to import environment variables' in call[0][1]
        ]
        assert len(warning_logs) > 0
