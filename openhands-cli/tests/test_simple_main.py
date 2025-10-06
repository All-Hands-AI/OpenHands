"""Tests for the simple main entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest


# Mock the imports that might not be available during testing
with patch.dict('sys.modules', {
    'openhands.sdk': MagicMock(),
    'openhands.sdk.conversation.state': MagicMock(),
    'openhands_cli.runner': MagicMock(),
    'openhands_cli.setup': MagicMock(),
    'openhands_cli.tui.settings.mcp_screen': MagicMock(),
    'openhands_cli.tui.settings.settings_screen': MagicMock(),
    'openhands_cli.tui.tui': MagicMock(),
    'openhands_cli.user_actions': MagicMock(),
    'openhands_cli.user_actions.utils': MagicMock(),
    'openhands_cli.agent_chat': MagicMock(),
    'openhands_cli.gui_launcher': MagicMock(),
}):
    from openhands_cli.simple_main import main


class TestMainFunction:
    """Test the main function with different command line arguments."""

    @pytest.mark.parametrize(
        "argv,expected_call_args,expected_launch_args",
        [
            # CLI mode tests
            (['openhands'], {'resume_conversation_id': None}, None),
            (['openhands', 'cli'], {'resume_conversation_id': None}, None),
            (['openhands', 'cli', '--resume', 'test-id'], {'resume_conversation_id': 'test-id'}, None),
            # Serve mode tests
            (['openhands', 'serve'], None, {'mount_cwd': False, 'gpu': False}),
            (['openhands', 'serve', '--mount-cwd'], None, {'mount_cwd': True, 'gpu': False}),
            (['openhands', 'serve', '--gpu'], None, {'mount_cwd': False, 'gpu': True}),
            (['openhands', 'serve', '--mount-cwd', '--gpu'], None, {'mount_cwd': True, 'gpu': True}),
        ],
    )
    def test_main_commands(self, argv, expected_call_args, expected_launch_args):
        """Test main function with various command line arguments."""
        with patch('sys.argv', argv):
            if expected_call_args is not None:
                # CLI mode test - mock the import at the module level
                with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
                    with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_cli:
                        main()
                        mock_run_cli.assert_called_once_with(**expected_call_args)
            else:
                # Serve mode test
                with patch('openhands_cli.gui_launcher.launch_gui_server') as mock_launch_gui:
                    main()
                    mock_launch_gui.assert_called_once_with(**expected_launch_args)

    @pytest.mark.parametrize(
        "argv,expected_exit_code",
        [
            (['openhands', 'invalid-command'], 2),  # Invalid command
            (['openhands', '--help'], 0),  # Help option
            (['openhands', 'serve', '--help'], 0),  # Serve help option
        ],
    )
    def test_main_exit_scenarios(self, argv, expected_exit_code):
        """Test scenarios where main exits with specific codes."""
        with patch('sys.argv', argv):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == expected_exit_code

