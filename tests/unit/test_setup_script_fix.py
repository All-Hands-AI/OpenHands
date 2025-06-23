"""
Tests for the setup script hanging fix.

This module tests the fix for issue #9197 where complex .openhands/setup.sh scripts
cause OpenHands agents to become non-functional due to hanging processes.
"""

from unittest.mock import MagicMock

import pytest

from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
)
from openhands.runtime.base import Runtime


class TestSetupScriptFix:
    """Test cases for the setup script hanging fix."""

    @pytest.fixture
    def mock_runtime(self):
        """Create a mock runtime for testing."""
        runtime = MagicMock(spec=Runtime)
        runtime.log = MagicMock()
        runtime.status_callback = None
        return runtime

    def test_maybe_run_setup_script_runs_in_subshell(self, mock_runtime):
        """Test that maybe_run_setup_script runs in a subshell."""
        # Mock the read operation to return a successful observation
        mock_runtime.read.return_value = MagicMock(spec=FileReadObservation)

        # Mock successful execution
        mock_obs = MagicMock(spec=CmdOutputObservation)
        mock_obs.exit_code = 0
        mock_obs.content = 'OPENHANDS_SETUP_COMPLETE\nOPENHANDS_SETUP_SUCCESS'
        mock_runtime.run_action.return_value = mock_obs

        # Call the method
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that run_action was called with subshell command
        mock_runtime.run_action.assert_called_once()
        action = mock_runtime.run_action.call_args[0][0]
        assert action.blocking is True
        assert 'chmod +x .openhands/setup.sh' in action.command
        assert 'source .openhands/setup.sh' in action.command
        assert 'OPENHANDS_SETUP_SUCCESS' in action.command

    def test_maybe_run_setup_script_with_complex_script(self, mock_runtime):
        """Test that maybe_run_setup_script handles complex scripts properly."""
        # Mock the read operation to return a successful observation
        mock_runtime.read.return_value = MagicMock(spec=FileReadObservation)

        # Mock successful execution of complex script
        mock_obs = MagicMock(spec=CmdOutputObservation)
        mock_obs.exit_code = 0
        mock_obs.content = 'Installing dependencies...\nOPENHANDS_SETUP_COMPLETE\nOPENHANDS_SETUP_SUCCESS'
        mock_runtime.run_action.return_value = mock_obs

        # Call the method
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that the script was executed successfully
        mock_runtime.run_action.assert_called_once()
        mock_runtime.log.assert_called_with(
            'info', 'Setup script completed successfully'
        )

    def test_maybe_run_setup_script_handles_errors(self, mock_runtime):
        """Test that maybe_run_setup_script handles errors properly."""
        # Mock the read operation to return a successful observation
        mock_runtime.read.return_value = MagicMock(spec=FileReadObservation)

        # Mock failed execution
        mock_obs = MagicMock(spec=CmdOutputObservation)
        mock_obs.exit_code = 1
        mock_obs.content = 'Setup failed'
        mock_runtime.run_action.return_value = mock_obs

        # Call the method
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that error was logged
        mock_runtime.log.assert_called_with(
            'error', 'Setup script failed with exit code 1: Setup failed'
        )

    def test_maybe_run_setup_script_no_script(self, mock_runtime):
        """Test that maybe_run_setup_script handles missing script gracefully."""
        # Mock the read operation to return an error (file not found)
        mock_runtime.read.return_value = MagicMock(spec=ErrorObservation)

        # Call the method
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that no further actions were taken
        mock_runtime.run_action.assert_not_called()

    def test_maybe_run_setup_script_incomplete_execution(self, mock_runtime):
        """Test that maybe_run_setup_script handles incomplete execution."""
        # Mock the read operation to return a successful observation
        mock_runtime.read.return_value = MagicMock(spec=FileReadObservation)

        # Mock execution that doesn't complete properly
        mock_obs = MagicMock(spec=CmdOutputObservation)
        mock_obs.exit_code = 0
        mock_obs.content = 'Some output but no success marker'
        mock_runtime.run_action.return_value = mock_obs

        # Call the method
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that error was logged
        mock_runtime.log.assert_called_with(
            'error',
            'Setup script did not complete successfully: Some output but no success marker',
        )

    def test_maybe_run_setup_script_non_cmd_observation(self, mock_runtime):
        """Test that maybe_run_setup_script handles non-CmdOutputObservation."""
        # Mock the read operation to return a successful observation
        mock_runtime.read.return_value = MagicMock(spec=FileReadObservation)

        # Mock execution that returns non-CmdOutputObservation
        mock_obs = MagicMock(spec=ErrorObservation)
        mock_runtime.run_action.return_value = mock_obs

        # Call the method
        Runtime.maybe_run_setup_script(mock_runtime)

        # Verify that error was logged
        mock_runtime.log.assert_called_with(
            'error', f'Setup script execution failed: {mock_obs}'
        )
