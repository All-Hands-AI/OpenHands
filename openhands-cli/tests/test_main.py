"""Tests for main entry point functionality."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from openhands_cli import simple_main
from openhands_cli.simple_main import main



class TestMainEntryPoint:
    """Test the main entry point behavior."""

    @patch('openhands_cli.agent_chat.run_cli_entry')
    @patch('sys.argv', ['openhands'])
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

    @patch('openhands_cli.agent_chat.run_cli_entry')
    @patch('sys.argv', ['openhands'])
    def test_main_handles_import_error(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() handles ImportError gracefully."""
        mock_run_agent_chat.side_effect = ImportError('Missing dependency')

        # Should raise ImportError (re-raised after handling)
        with pytest.raises(ImportError) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == 'Missing dependency'

    @patch('openhands_cli.agent_chat.run_cli_entry')
    @patch('sys.argv', ['openhands'])
    def test_main_handles_keyboard_interrupt(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles KeyboardInterrupt gracefully."""
        # Mock run_cli_entry to raise KeyboardInterrupt
        mock_run_agent_chat.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch('openhands_cli.agent_chat.run_cli_entry')
    @patch('sys.argv', ['openhands'])
    def test_main_handles_eof_error(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() handles EOFError gracefully."""
        # Mock run_cli_entry to raise EOFError
        mock_run_agent_chat.side_effect = EOFError()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

    @patch('openhands_cli.agent_chat.run_cli_entry')
    @patch('sys.argv', ['openhands'])
    def test_main_handles_general_exception(
        self, mock_run_agent_chat: MagicMock
    ) -> None:
        """Test that main() handles general exceptions."""
        mock_run_agent_chat.side_effect = Exception('Unexpected error')

        # Should raise Exception (re-raised after handling)
        with pytest.raises(Exception) as exc_info:
            simple_main.main()

        assert str(exc_info.value) == 'Unexpected error'

    @patch('openhands_cli.agent_chat.run_cli_entry')
    @patch('sys.argv', ['openhands', '--resume', 'test-conversation-id'])
    def test_main_with_resume_argument(self, mock_run_agent_chat: MagicMock) -> None:
        """Test that main() passes resume conversation ID when provided."""
        # Mock run_cli_entry to raise KeyboardInterrupt to exit gracefully
        mock_run_agent_chat.side_effect = KeyboardInterrupt()

        # Should complete without raising an exception (graceful exit)
        simple_main.main()

        # Should call run_cli_entry with the provided resume conversation ID
        mock_run_agent_chat.assert_called_once_with(
            resume_conversation_id='test-conversation-id'
        )




@pytest.mark.parametrize(
    "argv,expected_kwargs",
    [
        (['openhands'], {"resume_conversation_id": None}),
        (['openhands', '--resume', 'test-id'], {"resume_conversation_id": 'test-id'}),
    ],
)
def test_main_cli_calls_run_cli_entry(monkeypatch, argv, expected_kwargs):
    # Patch sys.argv since main() takes no params
    monkeypatch.setattr(sys, "argv", argv, raising=False)

    called = {}
    fake_agent_chat = SimpleNamespace(
        run_cli_entry=lambda **kw: called.setdefault("kwargs", kw)
    )
    # Provide the symbol that main() will import
    monkeypatch.setitem(sys.modules, "openhands_cli.agent_chat", fake_agent_chat)

    # Execute (no SystemExit expected on success)
    main()
    assert called["kwargs"] == expected_kwargs


@pytest.mark.parametrize(
    "argv,expected_kwargs",
    [
        (['openhands', 'serve'], {"mount_cwd": False, "gpu": False}),
        (['openhands', 'serve', '--mount-cwd'], {"mount_cwd": True, "gpu": False}),
        (['openhands', 'serve', '--gpu'], {"mount_cwd": False, "gpu": True}),
        (['openhands', 'serve', '--mount-cwd', '--gpu'], {"mount_cwd": True, "gpu": True}),
    ],
)
def test_main_serve_calls_launch_gui_server(monkeypatch, argv, expected_kwargs):
    monkeypatch.setattr(sys, "argv", argv, raising=False)

    called = {}
    fake_gui = SimpleNamespace(
        launch_gui_server=lambda **kw: called.setdefault("kwargs", kw)
    )
    monkeypatch.setitem(sys.modules, "openhands_cli.gui_launcher", fake_gui)

    main()
    assert called["kwargs"] == expected_kwargs


@pytest.mark.parametrize(
    "argv,expected_exit_code",
    [
        (['openhands', 'invalid-command'], 2),  # argparse error
        (['openhands', '--help'], 0),           # top-level help
        (['openhands', 'serve', '--help'], 0),  # subcommand help
    ],
)
def test_help_and_invalid(monkeypatch, argv, expected_exit_code):
    monkeypatch.setattr(sys, "argv", argv, raising=False)
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == expected_exit_code
