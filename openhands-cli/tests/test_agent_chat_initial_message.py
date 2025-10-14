"""Tests for initial_user_message behavior in agent_chat.run_cli_entry."""

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

import openhands_cli.agent_chat as agent_chat


class _DummyConversation:
    def __init__(self, conv_id: str = "conv-123") -> None:
        self.id = conv_id
        # Minimal state placeholder if inspected in code paths we don't exercise
        self.state = SimpleNamespace(confirmation_mode=False)
        self.agent = SimpleNamespace()


class _DummySession:
    def __init__(self, raise_on_prompt: BaseException) -> None:
        self._ex = raise_on_prompt

    def prompt(self, *_args, **_kwargs):
        raise self._ex


class TestAgentChatInitialMessage:
    @patch("openhands_cli.agent_chat.ConversationRunner")
    @patch("openhands_cli.agent_chat.print_formatted_text")
    @patch("openhands_cli.agent_chat.UserConfirmation", SimpleNamespace(ACCEPT="ACCEPT"))
    @patch("openhands_cli.agent_chat.exit_session_confirmation")
    @patch("openhands_cli.agent_chat._print_exit_hint")
    @patch("openhands_cli.agent_chat.start_fresh_conversation")
    @patch("openhands_cli.agent_chat.get_session_prompter")
    @patch("openhands_cli.agent_chat.display_welcome")
    @patch("openhands_cli.agent_chat.SettingsScreen")
    def test_sends_initial_user_message_once(
        self,
        _mock_settings_screen: MagicMock,
        mock_display_welcome: MagicMock,
        mock_get_session: MagicMock,
        mock_start_fresh: MagicMock,
        _mock_exit_hint: MagicMock,
        mock_exit_confirm: MagicMock,
        _mock_print: MagicMock,
        mock_runner_cls: MagicMock,
    ) -> None:
        """When initial_user_message is provided, it is sent once via runner.process_message."""
        # Arrange
        mock_start_fresh.return_value = _DummyConversation()
        mock_exit_confirm.return_value = "ACCEPT"
        mock_get_session.return_value = _DummySession(KeyboardInterrupt())

        runner_instance = MagicMock()
        mock_runner_cls.return_value = runner_instance

        initial_text = "please do X"

        # Act
        agent_chat.run_cli_entry(resume_conversation_id=None, initial_user_message=initial_text)

        # Assert
        mock_display_welcome.assert_called_once_with("conv-123", False)
        assert runner_instance.process_message.call_count == 1
        # Inspect the Message argument
        sent_msg = runner_instance.process_message.call_args.args[0]
        assert sent_msg.role == "user"
        contents = sent_msg.content
        assert isinstance(contents, list) and len(contents) == 1
        assert contents[0].text == initial_text

    @patch("openhands_cli.agent_chat.ConversationRunner")
    @patch("openhands_cli.agent_chat.print_formatted_text")
    @patch("openhands_cli.agent_chat.UserConfirmation", SimpleNamespace(ACCEPT="ACCEPT"))
    @patch("openhands_cli.agent_chat.exit_session_confirmation")
    @patch("openhands_cli.agent_chat._print_exit_hint")
    @patch("openhands_cli.agent_chat.start_fresh_conversation")
    @patch("openhands_cli.agent_chat.get_session_prompter")
    @patch("openhands_cli.agent_chat.display_welcome")
    @patch("openhands_cli.agent_chat.SettingsScreen")
    def test_no_initial_message_does_not_send(
        self,
        _mock_settings_screen: MagicMock,
        mock_display_welcome: MagicMock,
        mock_get_session: MagicMock,
        mock_start_fresh: MagicMock,
        _mock_exit_hint: MagicMock,
        mock_exit_confirm: MagicMock,
        _mock_print: MagicMock,
        mock_runner_cls: MagicMock,
    ) -> None:
        """When no initial_user_message is provided, runner.process_message is not called before prompt."""
        # Arrange
        mock_start_fresh.return_value = _DummyConversation()
        mock_exit_confirm.return_value = "ACCEPT"
        mock_get_session.return_value = _DummySession(KeyboardInterrupt())

        runner_instance = MagicMock()
        mock_runner_cls.return_value = runner_instance

        # Act
        agent_chat.run_cli_entry(resume_conversation_id=None, initial_user_message=None)

        # Assert
        mock_display_welcome.assert_called_once_with("conv-123", False)
        runner_instance.process_message.assert_not_called()

    @patch("openhands_cli.agent_chat.ConversationRunner")
    @patch("openhands_cli.agent_chat.print_formatted_text")
    @patch("openhands_cli.agent_chat.UserConfirmation", SimpleNamespace(ACCEPT="ACCEPT"))
    @patch("openhands_cli.agent_chat.exit_session_confirmation")
    @patch("openhands_cli.agent_chat._print_exit_hint")
    @patch("openhands_cli.agent_chat.start_fresh_conversation")
    @patch("openhands_cli.agent_chat.get_session_prompter")
    @patch("openhands_cli.agent_chat.display_welcome")
    @patch("openhands_cli.agent_chat.SettingsScreen")
    def test_resume_flag_propagates_to_setup_and_welcome(
        self,
        _mock_settings_screen: MagicMock,
        mock_display_welcome: MagicMock,
        mock_get_session: MagicMock,
        mock_start_fresh: MagicMock,
        _mock_exit_hint: MagicMock,
        mock_exit_confirm: MagicMock,
        _mock_print: MagicMock,
        mock_runner_cls: MagicMock,
    ) -> None:
        """Resume ID is passed to start_fresh_conversation and reflected in display_welcome."""
        # Arrange
        mock_start_fresh.return_value = _DummyConversation("abc-001")
        mock_exit_confirm.return_value = "ACCEPT"
        mock_get_session.return_value = _DummySession(KeyboardInterrupt())
        mock_runner_cls.return_value = MagicMock()

        # Act
        agent_chat.run_cli_entry(resume_conversation_id="abc-001", initial_user_message=None)

        # Assert
        mock_start_fresh.assert_called_once_with("abc-001")
        mock_display_welcome.assert_called_once_with("abc-001", True)
