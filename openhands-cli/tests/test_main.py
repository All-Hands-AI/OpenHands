"""Tests for main entry point functionality."""

from unittest.mock import MagicMock, patch

import pytest

from openhands_cli import simple_main


class TestMainEntryPoint:
    """Test the main entry point behavior."""

    @patch("openhands_cli.agent_chat.run_cli_entry")
    def test_main_starts_agent_chat_directly(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() starts agent chat directly without menu."""
        mock_run_agent_chat.return_value = None

        # Should complete without raising an exception
        simple_main.main()

        # Should call run_agent_chat directly
        mock_run_agent_chat.assert_called_once()

    @patch("openhands_cli.agent_chat.run_cli_entry")
    def test_main_handles_import_error(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() handles ImportError gracefully."""
        mock_run_agent_chat.side_effect = ImportError("Missing dependency")

        # Should raise ImportError (no longer using sys.exit)
        with pytest.raises(ImportError) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == "Missing dependency"

    @patch("openhands_cli.agent_chat.run_cli_entry")
    def test_main_handles_keyboard_interrupt(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        mock_run_agent_chat.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch("openhands_cli.agent_chat.run_cli_entry")
    def test_main_handles_eof_error(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() handles EOFError gracefully."""
        mock_run_agent_chat.side_effect = EOFError()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch("openhands_cli.agent_chat.run_cli_entry")
    def test_main_handles_general_exception(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles general exceptions."""
        mock_run_agent_chat.side_effect = Exception("Unexpected error")

        # Should raise Exception (no longer using sys.exit)
        with pytest.raises(Exception) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == "Unexpected error"
