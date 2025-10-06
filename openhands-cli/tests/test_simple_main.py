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

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands'])
    def test_main_default_cli_mode(self, mock_run_cli):
        """Test that CLI mode is the default when no command is specified."""
        main()
        mock_run_cli.assert_called_once_with(resume_conversation_id=None)

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands', 'cli'])
    def test_main_explicit_cli_mode(self, mock_run_cli):
        """Test explicit CLI mode."""
        main()
        mock_run_cli.assert_called_once_with(resume_conversation_id=None)

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands', 'cli', '--resume', 'test-conversation-id'])
    def test_main_cli_mode_with_resume(self, mock_run_cli):
        """Test CLI mode with resume conversation ID."""
        main()
        mock_run_cli.assert_called_once_with(resume_conversation_id='test-conversation-id')

    @patch('openhands_cli.gui_launcher.launch_gui_server')
    @patch('sys.argv', ['openhands', 'serve'])
    def test_main_serve_mode(self, mock_launch_gui):
        """Test serve mode."""
        main()
        mock_launch_gui.assert_called_once_with(mount_cwd=False, gpu=False)

    @patch('openhands_cli.gui_launcher.launch_gui_server')
    @patch('sys.argv', ['openhands', 'serve', '--mount-cwd'])
    def test_main_serve_mode_with_mount_cwd(self, mock_launch_gui):
        """Test serve mode with mount-cwd option."""
        main()
        mock_launch_gui.assert_called_once_with(mount_cwd=True, gpu=False)

    @patch('openhands_cli.gui_launcher.launch_gui_server')
    @patch('sys.argv', ['openhands', 'serve', '--gpu'])
    def test_main_serve_mode_with_gpu(self, mock_launch_gui):
        """Test serve mode with GPU option."""
        main()
        mock_launch_gui.assert_called_once_with(mount_cwd=False, gpu=True)

    @patch('openhands_cli.gui_launcher.launch_gui_server')
    @patch('sys.argv', ['openhands', 'serve', '--mount-cwd', '--gpu'])
    def test_main_serve_mode_with_all_options(self, mock_launch_gui):
        """Test serve mode with all options."""
        main()
        mock_launch_gui.assert_called_once_with(mount_cwd=True, gpu=True)

    @patch('sys.argv', ['openhands', 'invalid-command'])
    def test_main_invalid_command(self):
        """Test that invalid command shows help and exits."""
        with patch('sys.exit') as mock_exit:
            with patch('openhands_cli.simple_main.print_formatted_text'):
                main()
        mock_exit.assert_called_once_with(1)

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands', 'cli'])
    def test_main_import_error(self, mock_run_cli):
        """Test handling of ImportError."""
        mock_run_cli.side_effect = ImportError('Missing dependency')
        
        with pytest.raises(ImportError):
            with patch('openhands_cli.simple_main.print_formatted_text'):
                main()

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands', 'cli'])
    def test_main_keyboard_interrupt(self, mock_run_cli):
        """Test handling of KeyboardInterrupt."""
        mock_run_cli.side_effect = KeyboardInterrupt()
        
        with patch('openhands_cli.simple_main.print_formatted_text') as mock_print:
            main()
        
        # Should print goodbye message
        mock_print.assert_called()

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands', 'cli'])
    def test_main_eof_error(self, mock_run_cli):
        """Test handling of EOFError."""
        mock_run_cli.side_effect = EOFError()
        
        with patch('openhands_cli.simple_main.print_formatted_text') as mock_print:
            main()
        
        # Should print goodbye message
        mock_print.assert_called()

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands', 'cli'])
    def test_main_general_exception(self, mock_run_cli):
        """Test handling of general exceptions."""
        mock_run_cli.side_effect = Exception('Something went wrong')
        
        with pytest.raises(Exception):
            with patch('openhands_cli.simple_main.print_formatted_text'):
                with patch('traceback.print_exc'):
                    main()

    @patch('sys.argv', ['openhands', '--help'])
    def test_main_help_option(self):
        """Test that help option works."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # argparse exits with code 0 for help
        assert exc_info.value.code == 0

    @patch('sys.argv', ['openhands', 'serve', '--help'])
    def test_serve_help_option(self):
        """Test that serve help option works."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # argparse exits with code 0 for help
        assert exc_info.value.code == 0