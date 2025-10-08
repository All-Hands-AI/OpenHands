"""Test the first-time user settings flow."""

from unittest.mock import patch

from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.user_actions.settings_action import SettingsType


def test_first_time_settings_type_confirmation():
    """Test that first-time users get a different, more welcoming prompt."""
    from openhands_cli.user_actions.settings_action import settings_type_confirmation

    with patch('openhands_cli.user_actions.settings_action.cli_confirm') as mock_confirm:
        # Test basic selection for first-time users
        mock_confirm.return_value = 0  # Select first option (Basic)
        result = settings_type_confirmation(first_time=True)

        assert result == SettingsType.BASIC

        # Verify the prompt is different for first-time users
        call_args = mock_confirm.call_args
        question = call_args[0][0]
        choices = call_args[0][1]

        assert 'Welcome to OpenHands!' in question
        assert 'Basic Setup (Recommended)' in choices[0]
        assert 'Advanced Setup' in choices[1]
        assert len(choices) == 2  # No "Go back" option for first-time users


def test_first_time_settings_type_confirmation_advanced():
    """Test that first-time users can choose advanced settings."""
    from openhands_cli.user_actions.settings_action import settings_type_confirmation

    with patch('openhands_cli.user_actions.settings_action.cli_confirm') as mock_confirm:
        # Test advanced selection for first-time users
        mock_confirm.return_value = 1  # Select second option (Advanced)
        result = settings_type_confirmation(first_time=True)

        assert result == SettingsType.ADVANCED


def test_configure_first_time_settings_basic():
    """Test that configure_first_time_settings works for basic settings."""
    screen = SettingsScreen()

    with (
        patch(
            'openhands_cli.tui.settings.settings_screen.settings_type_confirmation',
            return_value=SettingsType.BASIC,
        ) as mock_type_confirm,
        patch.object(screen, 'handle_basic_settings') as mock_basic,
    ):
        screen.configure_first_time_settings()

        # Verify first_time=True was passed to settings_type_confirmation
        mock_type_confirm.assert_called_once_with(first_time=True)

        # Verify basic settings was called with escapable=False
        mock_basic.assert_called_once_with(escapable=False)


def test_configure_first_time_settings_advanced():
    """Test that configure_first_time_settings works for advanced settings."""
    screen = SettingsScreen()

    with (
        patch(
            'openhands_cli.tui.settings.settings_screen.settings_type_confirmation',
            return_value=SettingsType.ADVANCED,
        ) as mock_type_confirm,
        patch.object(screen, 'handle_advanced_settings') as mock_advanced,
    ):
        screen.configure_first_time_settings()

        # Verify first_time=True was passed to settings_type_confirmation
        mock_type_confirm.assert_called_once_with(first_time=True)

        # Verify advanced settings was called with escapable=False
        mock_advanced.assert_called_once_with(escapable=False)


def test_configure_first_time_settings_keyboard_interrupt_fallback():
    """Test that KeyboardInterrupt during first-time setup falls back to basic settings."""
    screen = SettingsScreen()

    with (
        patch(
            'openhands_cli.tui.settings.settings_screen.settings_type_confirmation',
            side_effect=KeyboardInterrupt(),
        ),
        patch.object(screen, 'handle_basic_settings') as mock_basic,
        patch('openhands_cli.tui.settings.settings_screen.print_formatted_text') as mock_print,
    ):
        screen.configure_first_time_settings()

        # Verify fallback message was printed
        mock_print.assert_called()

        # Verify basic settings was called with escapable=False as fallback
        mock_basic.assert_called_once_with(escapable=False)


def test_first_time_vs_returning_user_prompts():
    """Test that first-time and returning users get different prompts."""
    from openhands_cli.user_actions.settings_action import settings_type_confirmation

    with patch('openhands_cli.user_actions.settings_action.cli_confirm') as mock_confirm:
        # Test first-time user prompt
        mock_confirm.return_value = 0
        settings_type_confirmation(first_time=True)
        first_time_call = mock_confirm.call_args

        # Reset mock
        mock_confirm.reset_mock()

        # Test returning user prompt
        mock_confirm.return_value = 0
        settings_type_confirmation(first_time=False)
        returning_user_call = mock_confirm.call_args

        # Verify different questions
        first_time_question = first_time_call[0][0]
        returning_user_question = returning_user_call[0][0]

        assert first_time_question != returning_user_question
        assert 'Welcome to OpenHands!' in first_time_question
        assert 'Which settings would you like to modify?' in returning_user_question

        # Verify different choices
        first_time_choices = first_time_call[0][1]
        returning_user_choices = returning_user_call[0][1]

        assert len(first_time_choices) == 2  # No "Go back" option
        assert len(returning_user_choices) == 3  # Has "Go back" option
        assert 'Go back' in returning_user_choices
        assert 'Go back' not in first_time_choices
