"""Tests for main entry point functionality."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from openhands_cli import simple_main


class TestMainEntryPoint:
    """Test the main entry point behavior."""

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands-cli'])
    def test_main_starts_agent_chat_directly(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() starts agent chat directly when setup succeeds."""
        # Mock run_cli_entry to raise KeyboardInterrupt to exit gracefully
        mock_run_agent_chat.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

        # Should call run_cli_entry with no resume conversation ID
        mock_run_agent_chat.assert_called_once_with(resume_conversation_id=None)

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands-cli'])
    def test_main_handles_import_error(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() handles ImportError gracefully."""
        mock_run_agent_chat.side_effect = ImportError('Missing dependency')

        # Should raise ImportError (re-raised after handling)
        with pytest.raises(ImportError) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == 'Missing dependency'

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands-cli'])
    def test_main_handles_keyboard_interrupt(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        # Mock run_cli_entry to raise KeyboardInterrupt
        mock_run_agent_chat.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands-cli'])
    def test_main_handles_eof_error(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles EOFError gracefully."""
        # Mock run_cli_entry to raise EOFError
        mock_run_agent_chat.side_effect = EOFError()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands-cli'])
    def test_main_handles_general_exception(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles general exceptions."""
        mock_run_agent_chat.side_effect = Exception('Unexpected error')

        # Should raise Exception (re-raised after handling)
        with pytest.raises(Exception) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == 'Unexpected error'

    @patch('openhands_cli.simple_main.run_cli_entry')
    @patch('sys.argv', ['openhands-cli', '--resume', 'test-conversation-id'])
    def test_main_with_resume_argument(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() passes resume conversation ID when provided."""
        # Mock run_cli_entry to raise KeyboardInterrupt to exit gracefully
        mock_run_agent_chat.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

        # Should call run_cli_entry with the provided resume conversation ID
        mock_run_agent_chat.assert_called_once_with(resume_conversation_id='test-conversation-id')
