"""Tests for main entry point functionality."""

from unittest.mock import MagicMock, patch

import pytest
from openhands_cli import simple_main


class TestMainEntryPoint:
    """Test the main entry point behavior."""

    @patch('sys.argv', ['openhands'])
    def test_main_starts_agent_chat_directly(self) -> None:
        """Test that main() starts agent chat directly when setup succeeds."""
        with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
            with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_agent_chat:
                # Mock run_cli_entry to raise KeyboardInterrupt to exit gracefully
                mock_run_agent_chat.side_effect = KeyboardInterrupt()

                # Should complete without raising an exception (graceful exit)
                simple_main.main()

                # Should call run_cli_entry with no resume conversation ID
                mock_run_agent_chat.assert_called_once_with(resume_conversation_id=None)

    @patch('sys.argv', ['openhands'])
    def test_main_handles_import_error(self) -> None:
        """Test that main() handles ImportError gracefully."""
        with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
            with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_agent_chat:
                mock_run_agent_chat.side_effect = ImportError('Missing dependency')

                # Should raise ImportError (re-raised after handling)
                with pytest.raises(ImportError) as exc_info:
                    simple_main.main()

                assert str(exc_info.value) == 'Missing dependency'

    @patch('sys.argv', ['openhands'])
    def test_main_handles_keyboard_interrupt(self) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
            with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_agent_chat:
                # Mock run_cli_entry to raise KeyboardInterrupt
                mock_run_agent_chat.side_effect = KeyboardInterrupt()

                # Should complete without raising an exception (graceful exit)
                simple_main.main()

    @patch('sys.argv', ['openhands'])
    def test_main_handles_eof_error(self) -> None:
        """Test that main() handles EOFError gracefully."""
        with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
            with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_agent_chat:
                # Mock run_cli_entry to raise EOFError
                mock_run_agent_chat.side_effect = EOFError()

                # Should complete without raising an exception (graceful exit)
                simple_main.main()

    @patch('sys.argv', ['openhands'])
    def test_main_handles_general_exception(self) -> None:
        """Test that main() handles general exceptions."""
        with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
            with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_agent_chat:
                mock_run_agent_chat.side_effect = Exception('Unexpected error')

                # Should raise Exception (re-raised after handling)
                with pytest.raises(Exception) as exc_info:
                    simple_main.main()

                assert str(exc_info.value) == 'Unexpected error'

    @patch('sys.argv', ['openhands', 'cli', '--resume', 'test-conversation-id'])
    def test_main_with_resume_argument(self) -> None:
        """Test that main() passes resume conversation ID when provided."""
        with patch.dict('sys.modules', {'openhands_cli.agent_chat': MagicMock()}):
            with patch('openhands_cli.agent_chat.run_cli_entry') as mock_run_agent_chat:
                # Mock run_cli_entry to raise KeyboardInterrupt to exit gracefully
                mock_run_agent_chat.side_effect = KeyboardInterrupt()

                # Should complete without raising an exception (graceful exit)
                simple_main.main()

                # Should call run_cli_entry with the provided resume conversation ID
                mock_run_agent_chat.assert_called_once_with(
                    resume_conversation_id='test-conversation-id'
                )
