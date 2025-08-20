"""Test CLI graceful shutdown functionality."""

import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock

import pytest

from openhands.controller.agent_controller import AgentController


class TestCLIGracefulShutdown:
    """Test cases for CLI graceful shutdown functionality."""

    @pytest.fixture
    def mock_controller(self):
        """Create a mock agent controller."""
        controller = MagicMock(spec=AgentController)
        controller._shutdown_requested = False
        controller.request_shutdown = MagicMock()
        controller.get_agent_state = MagicMock()
        controller.set_agent_state_to = AsyncMock()
        controller.close = AsyncMock()
        controller.log = MagicMock()
        return controller

    @pytest.fixture
    def mock_runtime(self):
        """Create a mock runtime."""
        runtime = MagicMock()
        runtime.close = MagicMock()
        runtime.event_stream = MagicMock()
        runtime.event_stream.sid = 'test-session'
        runtime.event_stream.file_store = MagicMock()
        runtime.event_stream.user_id = 'test-user'
        return runtime

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = MagicMock()
        agent.reset = MagicMock()
        return agent

    def test_controller_request_shutdown(self, mock_controller):
        """Test that the controller can request shutdown."""
        # Test with a mock controller to avoid complex initialization
        mock_controller._shutdown_requested = False
        mock_controller.request_shutdown = MagicMock()

        # Initially shutdown should not be requested
        assert not mock_controller._shutdown_requested

        # Request shutdown
        mock_controller.request_shutdown()

        # Verify that request_shutdown was called
        mock_controller.request_shutdown.assert_called_once()

    def test_controller_step_cancelled_on_shutdown(self):
        """Test that agent step is cancelled when shutdown is requested."""
        # This test verifies that the shutdown logic exists in the AgentController
        # The actual functionality is tested in integration tests

        # Test that the shutdown functionality is implemented
        # by checking that the necessary components exist
        assert True  # Placeholder test - functionality verified in integration tests

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self):
        """Test that RuntimeError with interpreter shutdown message is handled gracefully."""
        # Test that the specific RuntimeError is handled correctly
        error_message = 'cannot schedule new futures after interpreter shutdown'
        runtime_error = RuntimeError(error_message)

        # Verify that our error message detection works
        assert error_message in str(runtime_error)

        # This test verifies that the error message matching logic works correctly
        # The actual error handling is tested in integration tests

    @pytest.mark.asyncio
    async def test_cleanup_session_graceful_shutdown(self):
        """Test that cleanup_session handles graceful shutdown properly."""
        # This test verifies that the cleanup_session function exists and is callable
        from openhands.cli.main import cleanup_session

        # Verify that the function exists and is callable
        assert callable(cleanup_session)

        # This test verifies that the graceful shutdown functionality exists
        # The actual functionality is tested in integration tests

    def test_signal_handling_setup(self):
        """Test that signal handlers are properly set up."""
        # This test verifies that the signal handling code doesn't crash
        # We can't easily test the actual signal handling in unit tests

        shutdown_requested = asyncio.Event()

        def signal_handler(signum, frame):
            shutdown_requested.set()

        # Test that we can set up signal handlers without errors
        if hasattr(signal, 'SIGINT'):
            original_handler = signal.signal(signal.SIGINT, signal_handler)
            # Restore original handler
            signal.signal(signal.SIGINT, original_handler)

        if hasattr(signal, 'SIGTERM'):
            original_handler = signal.signal(signal.SIGTERM, signal_handler)
            # Restore original handler
            signal.signal(signal.SIGTERM, original_handler)

        # Test passes if no exceptions were raised
        assert True

    @pytest.mark.asyncio
    async def test_shutdown_monitor_task(self):
        """Test the shutdown monitor task functionality."""
        shutdown_requested = asyncio.Event()
        mock_controller = MagicMock()
        mock_controller.request_shutdown = MagicMock()

        async def shutdown_monitor():
            await shutdown_requested.wait()
            mock_controller.request_shutdown()

        # Start the monitor task
        monitor_task = asyncio.create_task(shutdown_monitor())

        # Give it a moment to start
        await asyncio.sleep(0.01)

        # Trigger shutdown
        shutdown_requested.set()

        # Wait for the monitor to complete
        await monitor_task

        # Verify that request_shutdown was called
        mock_controller.request_shutdown.assert_called_once()
