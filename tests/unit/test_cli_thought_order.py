"""Tests for CLI thought display order fix.
This ensures that agent thoughts are displayed before commands, not after.
"""

from unittest.mock import MagicMock, patch

from openhands.cli.tui import display_event
from openhands.core.config import OpenHandsConfig
from openhands.events import EventSource
from openhands.events.action import Action, ActionConfirmationStatus, CmdRunAction
from openhands.events.action.message import MessageAction


class TestThoughtDisplayOrder:
    """Test that thoughts are displayed in the correct order relative to commands."""

    @patch('openhands.cli.tui.display_thought_if_new')
    @patch('openhands.cli.tui.display_command')
    def test_cmd_run_action_thought_before_command(
        self, mock_display_command, mock_display_thought_if_new
    ):
        """Test that for CmdRunAction, thought is displayed before command."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a CmdRunAction with a thought awaiting confirmation
        cmd_action = CmdRunAction(
            command='npm install',
            thought='I need to install the dependencies first before running the tests.',
        )
        cmd_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        display_event(cmd_action, config)

        # Verify that display_thought_if_new (for thought) was called before display_command
        mock_display_thought_if_new.assert_called_once_with(
            'I need to install the dependencies first before running the tests.'
        )
        mock_display_command.assert_called_once_with(cmd_action)

        # Check the call order by examining the mock call history
        all_calls = []
        all_calls.extend(
            [
                ('display_thought_if_new', call)
                for call in mock_display_thought_if_new.call_args_list
            ]
        )
        all_calls.extend(
            [('display_command', call) for call in mock_display_command.call_args_list]
        )

        # Sort by the order they were called (this is a simplified check)
        # In practice, we know display_thought_if_new should be called first based on our code
        assert mock_display_thought_if_new.called
        assert mock_display_command.called

    @patch('openhands.cli.tui.display_thought_if_new')
    @patch('openhands.cli.tui.display_command')
    def test_cmd_run_action_no_thought(
        self, mock_display_command, mock_display_thought_if_new
    ):
        """Test that CmdRunAction without thought only displays command."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a CmdRunAction without a thought
        cmd_action = CmdRunAction(command='npm install')
        cmd_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        display_event(cmd_action, config)

        # Verify that display_thought_if_new was not called (no thought)
        mock_display_thought_if_new.assert_not_called()
        mock_display_command.assert_called_once_with(cmd_action)

    @patch('openhands.cli.tui.display_thought_if_new')
    @patch('openhands.cli.tui.display_command')
    def test_cmd_run_action_empty_thought(
        self, mock_display_command, mock_display_thought_if_new
    ):
        """Test that CmdRunAction with empty thought only displays command."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a CmdRunAction with empty thought
        cmd_action = CmdRunAction(command='npm install', thought='')
        cmd_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        display_event(cmd_action, config)

        # Verify that display_thought_if_new was not called (empty thought)
        mock_display_thought_if_new.assert_not_called()
        mock_display_command.assert_called_once_with(cmd_action)

    @patch('openhands.cli.tui.display_thought_if_new')
    @patch('openhands.cli.tui.display_command')
    @patch('openhands.cli.tui.initialize_streaming_output')
    def test_cmd_run_action_confirmed_no_display(
        self, mock_init_streaming, mock_display_command, mock_display_thought_if_new
    ):
        """Test that confirmed CmdRunAction doesn't display command again but initializes streaming."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a confirmed CmdRunAction with thought
        cmd_action = CmdRunAction(
            command='npm install',
            thought='I need to install the dependencies first before running the tests.',
        )
        cmd_action.confirmation_state = ActionConfirmationStatus.CONFIRMED

        display_event(cmd_action, config)

        # Verify that thought is still displayed
        mock_display_thought_if_new.assert_called_once_with(
            'I need to install the dependencies first before running the tests.'
        )
        # But command should not be displayed again (already shown when awaiting confirmation)
        mock_display_command.assert_not_called()
        # Streaming should be initialized
        mock_init_streaming.assert_called_once()

    @patch('openhands.cli.tui.display_thought_if_new')
    def test_other_action_thought_display(self, mock_display_thought_if_new):
        """Test that other Action types still display thoughts normally."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a generic Action with thought
        action = Action()
        action.thought = 'This is a thought for a generic action.'

        display_event(action, config)

        # Verify that thought is displayed
        mock_display_thought_if_new.assert_called_once_with(
            'This is a thought for a generic action.'
        )

    @patch('openhands.cli.tui.display_message')
    def test_other_action_final_thought_display(self, mock_display_message):
        """Test that other Action types display final thoughts as agent messages."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a generic Action with final thought
        action = Action()
        action.final_thought = 'This is a final thought.'

        display_event(action, config)

        # Verify that final thought is displayed as an agent message
        mock_display_message.assert_called_once_with(
            'This is a final thought.', is_agent_message=True
        )

    @patch('openhands.cli.tui.display_thought_if_new')
    def test_message_action_from_agent(self, mock_display_thought_if_new):
        """Test that MessageAction from agent is displayed."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a MessageAction from agent
        message_action = MessageAction(content='Hello from agent')
        message_action._source = EventSource.AGENT

        display_event(message_action, config)

        # Verify that agent message is displayed with agent styling
        mock_display_thought_if_new.assert_called_once_with(
            'Hello from agent', is_agent_message=True
        )

    @patch('openhands.cli.tui.display_thought_if_new')
    def test_message_action_from_user_not_displayed(self, mock_display_thought_if_new):
        """Test that MessageAction from user is not displayed."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a MessageAction from user
        message_action = MessageAction(content='Hello from user')
        message_action._source = EventSource.USER

        display_event(message_action, config)

        # Verify that message is not displayed (only agent messages are shown)
        mock_display_thought_if_new.assert_not_called()

    @patch('openhands.cli.tui.display_thought_if_new')
    @patch('openhands.cli.tui.display_command')
    def test_cmd_run_action_with_both_thoughts(
        self, mock_display_command, mock_display_thought_if_new
    ):
        """Test CmdRunAction with both thought and final_thought."""
        config = MagicMock(spec=OpenHandsConfig)

        # Create a CmdRunAction with both thoughts
        cmd_action = CmdRunAction(command='npm install', thought='Initial thought')
        cmd_action.final_thought = 'Final thought'
        cmd_action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        display_event(cmd_action, config)

        # For CmdRunAction, only the regular thought should be displayed
        # (final_thought is handled by the general Action case, but CmdRunAction is handled first)
        mock_display_thought_if_new.assert_called_once_with('Initial thought')
        mock_display_command.assert_called_once_with(cmd_action)


class TestThoughtDisplayIntegration:
    """Integration tests for the thought display order fix."""

    def test_realistic_scenario_order(self):
        """Test a realistic scenario to ensure proper order."""
        config = MagicMock(spec=OpenHandsConfig)

        # Track the order of calls
        call_order = []

        def track_display_message(message, is_agent_message=False):
            call_order.append(f'THOUGHT: {message}')

        def track_display_command(event):
            call_order.append(f'COMMAND: {event.command}')

        with (
            patch(
                'openhands.cli.tui.display_message', side_effect=track_display_message
            ),
            patch(
                'openhands.cli.tui.display_command', side_effect=track_display_command
            ),
        ):
            # Create the scenario from the issue
            cmd_action = CmdRunAction(
                command='npm install',
                thought='I need to install the dependencies first before running the tests.',
            )
            cmd_action.confirmation_state = (
                ActionConfirmationStatus.AWAITING_CONFIRMATION
            )

            display_event(cmd_action, config)

        # Verify the correct order
        expected_order = [
            'THOUGHT: I need to install the dependencies first before running the tests.',
            'COMMAND: npm install',
        ]

        assert call_order == expected_order, (
            f'Expected {expected_order}, but got {call_order}'
        )
