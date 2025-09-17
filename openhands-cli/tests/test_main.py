"""Tests for main entry point functionality."""

from unittest.mock import MagicMock, patch

import pytest

from openhands_cli import simple_main


class TestMainEntryPoint:
    """Test the main entry point behavior."""

    @patch('openhands_cli.agent_chat.setup_agent')
    @patch('openhands_cli.agent_chat.ConversationRunner')
    @patch('openhands_cli.agent_chat.PromptSession')
    def test_main_starts_agent_chat_directly(
        self, mock_prompt_session: MagicMock, mock_runner: MagicMock, mock_setup_agent: MagicMock
    ) -> None:
        """Test that main() starts agent chat directly when setup succeeds."""
        # Mock setup_agent to return a valid conversation
        mock_conversation = MagicMock()
        mock_setup_agent.return_value = mock_conversation
        
        # Mock prompt session to raise KeyboardInterrupt to exit the loop
        mock_prompt_session.return_value.prompt.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

        # Should call setup_agent
        mock_setup_agent.assert_called_once()

    @patch('openhands_cli.simple_main.run_cli_entry')
    def test_main_handles_import_error(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() handles ImportError gracefully."""
        mock_run_agent_chat.side_effect = ImportError('Missing dependency')

        # Should raise ImportError (re-raised after handling)
        with pytest.raises(ImportError) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == 'Missing dependency'

    @patch('openhands_cli.agent_chat.setup_agent')
    @patch('openhands_cli.agent_chat.ConversationRunner')
    @patch('openhands_cli.agent_chat.PromptSession')
    def test_main_handles_keyboard_interrupt(
        self, mock_prompt_session: MagicMock, mock_runner: MagicMock, mock_setup_agent: MagicMock
    ) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        # Mock setup_agent to return a valid conversation
        mock_conversation = MagicMock()
        mock_setup_agent.return_value = mock_conversation
        
        # Mock prompt session to raise KeyboardInterrupt
        mock_prompt_session.return_value.prompt.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch('openhands_cli.agent_chat.setup_agent')
    @patch('openhands_cli.agent_chat.ConversationRunner')
    @patch('openhands_cli.agent_chat.PromptSession')
    def test_main_handles_eof_error(
        self, mock_prompt_session: MagicMock, mock_runner: MagicMock, mock_setup_agent: MagicMock
    ) -> None:
        """Test that main() handles EOFError gracefully."""
        # Mock setup_agent to return a valid conversation
        mock_conversation = MagicMock()
        mock_setup_agent.return_value = mock_conversation
        
        # Mock prompt session to raise EOFError
        mock_prompt_session.return_value.prompt.side_effect = EOFError()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch('openhands_cli.simple_main.run_cli_entry')
    def test_main_handles_general_exception(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles general exceptions."""
        mock_run_agent_chat.side_effect = Exception('Unexpected error')

        # Should raise Exception (re-raised after handling)
        with pytest.raises(Exception) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == 'Unexpected error'
