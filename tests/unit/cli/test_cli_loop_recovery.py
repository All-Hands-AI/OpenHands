"""Tests for CLI loop recovery functionality."""

from unittest.mock import MagicMock, patch

import pytest

from openhands.cli.commands import handle_resume_command
from openhands.controller.agent_controller import AgentController
from openhands.controller.stuck import StuckDetector
from openhands.core.schema import AgentState
from openhands.events import EventSource
from openhands.events.action import LoopRecoveryAction, MessageAction
from openhands.events.stream import EventStream


class TestCliLoopRecoveryIntegration:
    """Integration tests for CLI loop recovery functionality."""

    @pytest.mark.asyncio
    async def test_loop_recovery_resume_option_1(self):
        """Test that resume option 1 triggers loop recovery with memory truncation."""
        # Create a mock agent controller with stuck analysis
        mock_controller = MagicMock(spec=AgentController)
        mock_controller._stuck_detector = MagicMock(spec=StuckDetector)
        mock_controller._stuck_detector.stuck_analysis = MagicMock()
        mock_controller._stuck_detector.stuck_analysis.loop_start_idx = 5

        # Mock the loop recovery methods
        mock_controller._perform_loop_recovery = MagicMock()
        mock_controller._restart_with_last_user_message = MagicMock()
        mock_controller.set_agent_state_to = MagicMock()
        mock_controller._loop_recovery_info = None

        # Create a mock event stream
        event_stream = MagicMock(spec=EventStream)

        # Call handle_resume_command with option 1
        close_repl, new_session_requested = await handle_resume_command(
            '/resume 1', event_stream, AgentState.PAUSED
        )

        # Verify that LoopRecoveryAction was added to the event stream
        event_stream.add_event.assert_called_once()
        args, kwargs = event_stream.add_event.call_args
        loop_recovery_action, source = args

        assert isinstance(loop_recovery_action, LoopRecoveryAction)
        assert loop_recovery_action.option == 1
        assert source == EventSource.USER

        # Check the return values
        assert close_repl is True
        assert new_session_requested is False

    @pytest.mark.asyncio
    async def test_loop_recovery_resume_option_2(self):
        """Test that resume option 2 triggers restart with last user message."""
        # Create a mock event stream
        event_stream = MagicMock(spec=EventStream)

        # Call handle_resume_command with option 2
        close_repl, new_session_requested = await handle_resume_command(
            '/resume 2', event_stream, AgentState.PAUSED
        )

        # Verify that LoopRecoveryAction was added to the event stream
        event_stream.add_event.assert_called_once()
        args, kwargs = event_stream.add_event.call_args
        loop_recovery_action, source = args

        assert isinstance(loop_recovery_action, LoopRecoveryAction)
        assert loop_recovery_action.option == 2
        assert source == EventSource.USER

        # Check the return values
        assert close_repl is True
        assert new_session_requested is False

    @pytest.mark.asyncio
    async def test_regular_resume_without_loop_recovery(self):
        """Test that regular resume without option sends continue message."""
        # Create a mock event stream
        event_stream = MagicMock(spec=EventStream)

        # Call handle_resume_command without loop recovery option
        close_repl, new_session_requested = await handle_resume_command(
            '/resume', event_stream, AgentState.PAUSED
        )

        # Verify that MessageAction was added to the event stream
        event_stream.add_event.assert_called_once()
        args, kwargs = event_stream.add_event.call_args
        message_action, source = args

        assert isinstance(message_action, MessageAction)
        assert message_action.content == 'continue'
        assert source == EventSource.USER

        # Check the return values
        assert close_repl is True
        assert new_session_requested is False

    @pytest.mark.asyncio
    async def test_handle_commands_with_loop_recovery_resume(self):
        """Test that handle_commands properly routes loop recovery resume commands."""
        from openhands.cli.commands import handle_commands

        # Create mock dependencies
        event_stream = MagicMock(spec=EventStream)
        usage_metrics = MagicMock()
        sid = 'test-session-id'
        config = MagicMock()
        current_dir = '/test/dir'
        settings_store = MagicMock()
        agent_state = AgentState.PAUSED

        # Mock handle_resume_command
        with patch(
            'openhands.cli.commands.handle_resume_command'
        ) as mock_handle_resume:
            mock_handle_resume.return_value = (False, False)

            # Call handle_commands with loop recovery resume
            close_repl, reload_microagents, new_session, _ = await handle_commands(
                '/resume 1',
                event_stream,
                usage_metrics,
                sid,
                config,
                current_dir,
                settings_store,
                agent_state,
            )

            # Check that handle_resume_command was called with correct args
            mock_handle_resume.assert_called_once_with(
                '/resume 1', event_stream, agent_state
            )

            # Check the return values
            assert close_repl is False
            assert reload_microagents is False
            assert new_session is False
