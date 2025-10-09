"""Tests for the /new command functionality."""

from unittest.mock import MagicMock, patch
from uuid import UUID
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.defaults import DummyOutput
from openhands_cli.setup import MissingAgentSpec, start_fresh_conversation
from openhands_cli.user_actions import UserConfirmation

@patch('openhands_cli.setup.setup_conversation')
def test_start_fresh_conversation_success(mock_setup_conversation):
    """Test that start_fresh_conversation creates a new conversation successfully."""
    # Mock the conversation object
    mock_conversation = MagicMock()
    mock_conversation.id = UUID('12345678-1234-5678-9abc-123456789abc')
    mock_setup_conversation.return_value = mock_conversation

    # Call the function
    result = start_fresh_conversation()

    # Verify the result
    assert result == mock_conversation
    mock_setup_conversation.assert_called_once_with(None)


@patch('openhands_cli.setup.SettingsScreen')
@patch('openhands_cli.setup.setup_conversation')
def test_start_fresh_conversation_missing_agent_spec(
    mock_setup_conversation,
    mock_settings_screen_class
):
    """Test that start_fresh_conversation handles MissingAgentSpec exception."""
    # Mock the SettingsScreen instance
    mock_settings_screen = MagicMock()
    mock_settings_screen_class.return_value = mock_settings_screen

    # Mock setup_conversation to raise MissingAgentSpec on first call, then succeed
    mock_conversation = MagicMock()
    mock_conversation.id = UUID('12345678-1234-5678-9abc-123456789abc')
    mock_setup_conversation.side_effect = [
        MissingAgentSpec("Agent spec missing"),
        mock_conversation
    ]

    # Call the function
    result = start_fresh_conversation()

    # Verify the result
    assert result == mock_conversation
    # Should be called twice: first fails, second succeeds
    assert mock_setup_conversation.call_count == 2
    # Settings screen should be called once with first_time=True (new behavior)
    mock_settings_screen.configure_settings.assert_called_once_with(first_time=True)





@patch('openhands_cli.agent_chat.exit_session_confirmation')
@patch('openhands_cli.agent_chat.get_session_prompter')
@patch('openhands_cli.agent_chat.setup_conversation')
@patch('openhands_cli.agent_chat.start_fresh_conversation')
@patch('openhands_cli.agent_chat.ConversationRunner')
def test_new_command_resets_confirmation_mode(
    mock_runner_cls,
    mock_start_fresh_conversation,
    mock_setup_conversation,
    mock_get_session_prompter,
    mock_exit_confirm,
):
    # Auto-accept the exit prompt to avoid interactive UI and EOFError
    mock_exit_confirm.return_value = UserConfirmation.ACCEPT

    conv1 = MagicMock(); conv1.id = UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
    conv2 = MagicMock(); conv2.id = UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
    mock_start_fresh_conversation.return_value = conv1
    mock_setup_conversation.side_effect = [conv2]

    # Distinct runner instances for each conversation
    runner1 = MagicMock(); runner1.is_confirmation_mode_active = True
    runner2 = MagicMock(); runner2.is_confirmation_mode_active = False
    mock_runner_cls.side_effect = [runner1, runner2]

    # Real session fed by a pipe (no interactive confirmation now)
    from openhands_cli.user_actions.utils import get_session_prompter as real_get_session_prompter
    with create_pipe_input() as pipe:
        output = DummyOutput()
        session = real_get_session_prompter(input=pipe, output=output)
        mock_get_session_prompter.return_value = session

        from openhands_cli.agent_chat import run_cli_entry
        # Trigger /new, then /status, then /exit (exit will be auto-accepted)
        for ch in "/new\r/exit\r":
            pipe.send_text(ch)

        run_cli_entry(None)

    # Assert we switched to a new runner for conv2
    assert mock_runner_cls.call_count == 2
    assert mock_runner_cls.call_args_list[0].args[0] is conv1
    assert mock_runner_cls.call_args_list[1].args[0] is conv2
