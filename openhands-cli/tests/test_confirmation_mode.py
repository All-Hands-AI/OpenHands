#!/usr/bin/env python3
"""
Tests for confirmation mode functionality in OpenHands CLI.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from openhands.sdk import ActionBase
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.defaults import DummyOutput

from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import setup_agent
from openhands_cli.user_actions import agent_action, ask_user_confirmation, utils
from openhands_cli.user_actions.types import UserConfirmation
from tests.utils import _send_keys


class MockAction(ActionBase):
    """Mock action schema for testing."""

    command: str


class TestConfirmationMode:
    """Test suite for confirmation mode functionality."""

    def test_setup_agent_creates_conversation(self) -> None:
        """Test that setup_agent creates a conversation successfully."""
        with patch.dict(os.environ, {"LITELLM_API_KEY": "test-key"}):
            with (
                patch("openhands_cli.setup.LLM"),
                patch("openhands_cli.setup.Agent"),
                patch("openhands_cli.setup.Conversation") as mock_conversation,
                patch("openhands_cli.setup.BashExecutor"),
                patch("openhands_cli.setup.FileEditorExecutor"),
            ):
                mock_conv_instance = MagicMock()
                mock_conversation.return_value = mock_conv_instance

                result = setup_agent()

                # Verify conversation was created and returned
                assert result == mock_conv_instance
                mock_conversation.assert_called_once()

    def test_conversation_runner_set_confirmation_mode(self) -> None:
        """Test that ConversationRunner can set confirmation mode."""

        mock_conversation = MagicMock()
        runner = ConversationRunner(mock_conversation)

        # Test enabling confirmation mode
        runner.set_confirmation_mode(True)
        assert runner.confirmation_mode is True
        mock_conversation.set_confirmation_mode.assert_called_with(True)

        # Test disabling confirmation mode
        runner.set_confirmation_mode(False)
        assert runner.confirmation_mode is False
        mock_conversation.set_confirmation_mode.assert_called_with(False)

    def test_conversation_runner_initial_state(self) -> None:
        """Test that ConversationRunner starts with confirmation mode disabled."""

        mock_conversation = MagicMock()
        runner = ConversationRunner(mock_conversation)

        # Verify initial state
        assert runner.confirmation_mode is False

    def test_setup_agent_without_api_key(self) -> None:
        """Test that setup_agent raises exception when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with (
                patch("openhands_cli.setup.print_formatted_text"),
                pytest.raises(Exception, match="No API key found"),
            ):
                setup_agent()

    def test_ask_user_confirmation_empty_actions(self) -> None:
        """Test that ask_user_confirmation returns ACCEPT for empty actions list."""
        result, reason = ask_user_confirmation([])
        assert result == UserConfirmation.ACCEPT
        assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_yes(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation returns ACCEPT when user selects yes."""
        mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "ls -la"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.ACCEPT
        assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_no(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation returns REJECT when user selects no."""
        mock_cli_confirm.return_value = 1  # Second option (No, reject)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "rm -rf /"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.REJECT
        assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_y_shorthand(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation accepts first option as yes."""
        mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "echo hello"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.ACCEPT
        assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_n_shorthand(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation accepts second option as no."""
        mock_cli_confirm.return_value = 1  # Second option (No, reject)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "dangerous command"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.REJECT
        assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_invalid_then_yes(
        self, mock_cli_confirm: Any
    ) -> None:
        """Test that ask_user_confirmation handles selection and accepts yes."""
        mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "echo test"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.ACCEPT
        assert reason == ""
        assert mock_cli_confirm.call_count == 1

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_keyboard_interrupt(
        self, mock_cli_confirm: Any
    ) -> None:
        """Test that ask_user_confirmation handles KeyboardInterrupt gracefully."""
        mock_cli_confirm.side_effect = KeyboardInterrupt()

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "echo test"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.DEFER
        assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_eof_error(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation handles EOFError gracefully."""
        mock_cli_confirm.side_effect = EOFError()

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "echo test"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.DEFER
        assert reason == ""

    def test_ask_user_confirmation_multiple_actions(self) -> None:
        """Test that ask_user_confirmation displays multiple actions correctly."""
        with (
            patch(
                "openhands_cli.user_actions.agent_action.cli_confirm"
            ) as mock_cli_confirm,
            patch(
                "openhands_cli.user_actions.agent_action.print_formatted_text"
            ) as mock_print,
        ):
            mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

            mock_action1 = MagicMock()
            mock_action1.tool_name = "bash"
            mock_action1.action = "ls -la"

            mock_action2 = MagicMock()
            mock_action2.tool_name = "str_replace_editor"
            mock_action2.action = "create file.txt"

            result, reason = ask_user_confirmation([mock_action1, mock_action2])
            assert result == UserConfirmation.ACCEPT
            assert reason == ""

            # Verify that both actions were displayed
            assert mock_print.call_count >= 3  # Header + 2 actions

    @patch("openhands_cli.user_actions.agent_action.prompt_user")
    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_no_with_reason(
        self, mock_cli_confirm: Any, mock_prompt_user: Any
    ) -> None:
        """Test that ask_user_confirmation returns REJECT when user selects 'No (with reason)'."""
        mock_cli_confirm.return_value = 2  # Third option (No, with reason)
        mock_prompt_user.return_value = ("This action is too risky", False)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "rm -rf /"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.REJECT
        assert reason == "This action is too risky"
        mock_prompt_user.assert_called_once()

    @patch("openhands_cli.user_actions.agent_action.prompt_user")
    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_no_with_reason_cancelled(
        self, mock_cli_confirm: Any, mock_prompt_user: Any
    ) -> None:
        """Test that ask_user_confirmation falls back to DEFER when reason input is cancelled."""
        mock_cli_confirm.return_value = 2  # Third option (No, with reason)
        mock_prompt_user.return_value = ("", True)  # User cancelled reason input

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "dangerous command"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.DEFER
        assert reason == ""
        mock_prompt_user.assert_called_once()

    def test_user_confirmation_is_escapable_e2e(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """E2E: non-escapable should ignore Ctrl-C/Ctrl-P/Esc; only Enter returns."""
        real_cli_confirm = utils.cli_confirm

        with create_pipe_input() as pipe:
            output = DummyOutput()

            def wrapper(
                question: str,
                choices: list[str] | None = None,
                initial_selection: int = 0,
                escapable: bool = False,
                **extra: object,
            ) -> int:
                # keep original params; inject test IO
                return real_cli_confirm(
                    question=question,
                    choices=choices,
                    initial_selection=initial_selection,
                    escapable=escapable,
                    input=pipe,
                    output=output,
                )

            # Patch the symbol the caller uses
            monkeypatch.setattr(agent_action, "cli_confirm", wrapper, raising=True)

            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(
                    ask_user_confirmation, [MockAction(command="echo hello world")]
                )

                _send_keys(pipe, "\x03")  # Ctrl-C (ignored)
                result, reason = fut.result(timeout=2.0)
                assert result == UserConfirmation.DEFER  # escaped confirmation view
                assert reason == ""

    @patch("openhands_cli.user_actions.agent_action.cli_confirm")
    def test_ask_user_confirmation_always_accept(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation returns ALWAYS_ACCEPT when user selects fourth option."""
        mock_cli_confirm.return_value = 3  # Fourth option (Always proceed)

        mock_action = MagicMock()
        mock_action.tool_name = "bash"
        mock_action.action = "echo test"

        result, reason = ask_user_confirmation([mock_action])
        assert result == UserConfirmation.ALWAYS_ACCEPT
        assert reason == ""

    def test_conversation_runner_handles_always_accept(self) -> None:
        """Test that ConversationRunner disables confirmation mode when ALWAYS_ACCEPT is returned."""
        mock_conversation = MagicMock()
        runner = ConversationRunner(mock_conversation)

        # Enable confirmation mode first
        runner.set_confirmation_mode(True)
        assert runner.confirmation_mode is True

        # Mock the conversation state to simulate waiting for confirmation
        mock_conversation.state.agent_waiting_for_confirmation = True
        mock_conversation.state.agent_finished = False

        # Mock get_unmatched_actions to return some actions
        with patch("openhands_cli.runner.get_unmatched_actions") as mock_get_actions:
            mock_action = MagicMock()
            mock_action.tool_name = "bash"
            mock_action.action = "echo test"
            mock_get_actions.return_value = [mock_action]

            # Mock ask_user_confirmation to return ALWAYS_ACCEPT
            with patch("openhands_cli.runner.ask_user_confirmation") as mock_ask:
                mock_ask.return_value = (UserConfirmation.ALWAYS_ACCEPT, "")

                # Mock print_formatted_text to avoid output during test
                with patch("openhands_cli.runner.print_formatted_text"):
                    result = runner._handle_confirmation_request()

                    # Verify that confirmation mode was disabled
                    assert result == UserConfirmation.ALWAYS_ACCEPT
                    assert runner.confirmation_mode is False
                    mock_conversation.set_confirmation_mode.assert_called_with(False)
