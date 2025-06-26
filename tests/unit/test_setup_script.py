"""Unit tests for setup script functionality."""

import unittest
from unittest.mock import MagicMock, patch

from openhands.core.config import OpenHandsConfig
from openhands.events import EventSource, EventStream
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.base import Runtime


class TestSetupScript(unittest.TestCase):
    """Test setup script functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = OpenHandsConfig()

        # Mock the EventStream
        self.event_stream = MagicMock(spec=EventStream)

        # Create a mock Runtime instead of a concrete subclass
        self.runtime = MagicMock(spec=Runtime)
        self.runtime.event_stream = self.event_stream
        self.runtime._setup_script_executed = False
        self.runtime.status_callback = None
        self.runtime.log = MagicMock()

        # Patch the maybe_run_setup_script method to use the real implementation
        self.original_method = Runtime.maybe_run_setup_script
        self.patcher = patch.object(
            Runtime, 'maybe_run_setup_script', self.original_method
        )
        self.mock_method = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_setup_script_sets_environment_source(self):
        """Test that setup script action has the correct source."""
        # Mock the read method to simulate a setup script exists
        mock_read_result = MagicMock(spec=CmdOutputObservation)
        mock_read_result.__class__ = CmdOutputObservation
        self.runtime.read.return_value = mock_read_result

        # Mock the run_action method
        mock_observation = MagicMock(spec=CmdOutputObservation)
        mock_observation.exit_code = 0
        self.runtime.run_action.return_value = mock_observation

        # Call the method under test
        self.original_method(self.runtime)

        # Verify that add_event was called with EventSource.ENVIRONMENT
        # First call should be for the action
        first_call = self.event_stream.add_event.call_args_list[0]
        self.assertEqual(first_call[0][1], EventSource.ENVIRONMENT)

        # Second call should be for the observation
        second_call = self.event_stream.add_event.call_args_list[1]
        self.assertEqual(second_call[0][1], EventSource.ENVIRONMENT)

        # Verify that run_action was called
        self.runtime.run_action.assert_called_once()

    def test_setup_script_not_executed_multiple_times(self):
        """Test that setup script is not executed multiple times."""
        # Mock the read method to simulate a setup script exists
        mock_read_result = MagicMock(spec=CmdOutputObservation)
        mock_read_result.__class__ = CmdOutputObservation
        self.runtime.read.return_value = mock_read_result

        # Mock the run_action method
        mock_observation = MagicMock(spec=CmdOutputObservation)
        mock_observation.exit_code = 0
        self.runtime.run_action.return_value = mock_observation

        # Call the method under test twice
        self.original_method(self.runtime)

        # Reset the mock to verify it's not called again
        self.runtime.run_action.reset_mock()

        # Call the method again
        self.original_method(self.runtime)

        # Verify run_action was not called the second time
        self.runtime.run_action.assert_not_called()


if __name__ == '__main__':
    unittest.main()
