#!/usr/bin/env python3
"""
Tests for confirmation mode functionality in OpenHands CLI.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest
from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import MissingAgentSpec, setup_conversation
from openhands_cli.user_actions import agent_action, ask_user_confirmation, utils
from openhands_cli.user_actions.types import ConfirmationResult, UserConfirmation
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.defaults import DummyOutput

from openhands.sdk import Action
from openhands.sdk.security.confirmation_policy import (
    AlwaysConfirm,
    ConfirmRisky,
    NeverConfirm,
    SecurityRisk,
)
from tests.utils import _send_keys


class MockAction(Action):
    """Mock action schema for testing."""

    command: str


class TestConfirmationMode:
    """Test suite for confirmation mode functionality."""

    def test_setup_conversation_creates_conversation(self) -> None:
        """Test that setup_conversation creates a conversation successfully."""
        with patch.dict(os.environ, {'LLM_MODEL': 'test-model'}):
            with (
                patch('openhands_cli.setup.Conversation') as mock_conversation_class,
                patch('openhands_cli.setup.AgentStore') as mock_agent_store_class,
                patch('openhands_cli.setup.print_formatted_text') as mock_print,
                patch('openhands_cli.setup.HTML'),
                patch('openhands_cli.setup.uuid') as mock_uuid,
            ):
                # Mock dependencies
                mock_conversation_id = MagicMock()
                mock_uuid.uuid4.return_value = mock_conversation_id

                # Mock AgentStore
                mock_agent_store_instance = MagicMock()
                mock_agent_instance = MagicMock()
                mock_agent_instance.llm.model = 'test-model'
                mock_agent_store_instance.load.return_value = mock_agent_instance
                mock_agent_store_class.return_value = mock_agent_store_instance

                # Mock Conversation constructor to return a mock conversation
                mock_conversation_instance = MagicMock()
                mock_conversation_class.return_value = mock_conversation_instance

                result = setup_conversation()

                # Verify conversation was created and returned
                assert result == mock_conversation_instance
                mock_agent_store_class.assert_called_once()
                mock_agent_store_instance.load.assert_called_once()
                mock_conversation_class.assert_called_once_with(
                    agent=mock_agent_instance,
                    workspace=ANY,
                    persistence_dir=ANY,
                    conversation_id=mock_conversation_id,
                )
                # Verify print_formatted_text was called
                mock_print.assert_called_once()

    def test_setup_conversation_raises_missing_agent_spec(self) -> None:
        """Test that setup_conversation raises MissingAgentSpec when agent is not found."""
        with (
            patch('openhands_cli.setup.AgentStore') as mock_agent_store_class,
        ):
            # Mock AgentStore to return None (no agent found)
            mock_agent_store_instance = MagicMock()
            mock_agent_store_instance.load.return_value = None
            mock_agent_store_class.return_value = mock_agent_store_instance

            # Should raise MissingAgentSpec
            with pytest.raises(MissingAgentSpec) as exc_info:
                setup_conversation()

            assert 'Agent specification not found' in str(exc_info.value)
            mock_agent_store_class.assert_called_once()
            mock_agent_store_instance.load.assert_called_once()

    def test_conversation_runner_set_confirmation_mode(self) -> None:
        """Test that ConversationRunner can set confirmation policy."""

        mock_conversation = MagicMock()
        mock_conversation.confirmation_policy_active = False
        mock_conversation.is_confirmation_mode_active = False
        runner = ConversationRunner(mock_conversation)

        # Test enabling confirmation mode
        runner.set_confirmation_policy(AlwaysConfirm())
        mock_conversation.set_confirmation_policy.assert_called_with(AlwaysConfirm())

        # Test disabling confirmation mode
        runner.set_confirmation_policy(NeverConfirm())
        mock_conversation.set_confirmation_policy.assert_called_with(NeverConfirm())

    def test_conversation_runner_initial_state(self) -> None:
        """Test that ConversationRunner starts with confirmation mode disabled."""

        mock_conversation = MagicMock()
        mock_conversation.confirmation_policy_active = False
        mock_conversation.is_confirmation_mode_active = False
        runner = ConversationRunner(mock_conversation)

        # Verify initial state
        assert runner.is_confirmation_mode_active is False

    def test_ask_user_confirmation_empty_actions(self) -> None:
        """Test that ask_user_confirmation returns ACCEPT for empty actions list."""
        result = ask_user_confirmation([])
        assert isinstance(result, ConfirmationResult)
        assert result.decision == UserConfirmation.ACCEPT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        assert result.policy_change is None

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_yes(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation returns ACCEPT when user selects yes."""
        mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'ls -la'

        result = ask_user_confirmation([mock_action])
        assert isinstance(result, ConfirmationResult)
        assert result.decision == UserConfirmation.ACCEPT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        assert result.policy_change is None

    @patch('openhands_cli.user_actions.agent_action.cli_text_input')
    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_no(self, mock_cli_confirm: Any, mock_cli_text_input: Any) -> None:
        """Test that ask_user_confirmation returns REJECT when user selects reject without reason."""
        mock_cli_confirm.return_value = 1  # Second option (Reject)
        mock_cli_text_input.return_value = ''  # Empty reason (reject without reason)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'rm -rf /'

        result = ask_user_confirmation([mock_action])
        assert isinstance(result, ConfirmationResult)
        assert result.decision == UserConfirmation.REJECT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once_with('Reason (and let OpenHands know why): ')

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_y_shorthand(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation accepts first option as yes."""
        mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'echo hello'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.ACCEPT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None

    @patch('openhands_cli.user_actions.agent_action.cli_text_input')
    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_n_shorthand(self, mock_cli_confirm: Any, mock_cli_text_input: Any) -> None:
        """Test that ask_user_confirmation accepts second option as reject."""
        mock_cli_confirm.return_value = 1  # Second option (Reject)
        mock_cli_text_input.return_value = ''  # Empty reason (reject without reason)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'dangerous command'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.REJECT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once_with('Reason (and let OpenHands know why): ')

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_invalid_then_yes(
        self, mock_cli_confirm: Any
    ) -> None:
        """Test that ask_user_confirmation handles selection and accepts yes."""
        mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'echo test'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.ACCEPT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        assert mock_cli_confirm.call_count == 1

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_keyboard_interrupt(
        self, mock_cli_confirm: Any
    ) -> None:
        """Test that ask_user_confirmation handles KeyboardInterrupt gracefully."""
        mock_cli_confirm.side_effect = KeyboardInterrupt()

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'echo test'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.DEFER
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_eof_error(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation handles EOFError gracefully."""
        mock_cli_confirm.side_effect = EOFError()

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'echo test'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.DEFER
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None

    def test_ask_user_confirmation_multiple_actions(self) -> None:
        """Test that ask_user_confirmation displays multiple actions correctly."""
        with (
            patch(
                'openhands_cli.user_actions.agent_action.cli_confirm'
            ) as mock_cli_confirm,
            patch(
                'openhands_cli.user_actions.agent_action.print_formatted_text'
            ) as mock_print,
        ):
            mock_cli_confirm.return_value = 0  # First option (Yes, proceed)

            mock_action1 = MagicMock()
            mock_action1.tool_name = 'bash'
            mock_action1.action = 'ls -la'

            mock_action2 = MagicMock()
            mock_action2.tool_name = 'str_replace_editor'
            mock_action2.action = 'create file.txt'

            result = ask_user_confirmation([mock_action1, mock_action2])
            assert isinstance(result, ConfirmationResult)
            assert result.decision == UserConfirmation.ACCEPT
            assert result.reason == ''
            assert result.policy_change is None

            # Verify that both actions were displayed
            assert mock_print.call_count >= 3  # Header + 2 actions

    @patch('openhands_cli.user_actions.agent_action.cli_text_input')
    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_no_with_reason(
        self, mock_cli_confirm: Any, mock_cli_text_input: Any
    ) -> None:
        """Test that ask_user_confirmation returns REJECT when user selects 'Reject' and provides a reason."""
        mock_cli_confirm.return_value = 1  # Second option (Reject)
        mock_cli_text_input.return_value = 'This action is too risky'

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'rm -rf /'

        result = ask_user_confirmation([mock_action])
        assert isinstance(result, ConfirmationResult)
        assert result.decision == UserConfirmation.REJECT
        assert result.reason == 'This action is too risky'
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once_with('Reason (and let OpenHands know why): ')

    @patch('openhands_cli.user_actions.agent_action.cli_text_input')
    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_no_with_reason_cancelled(
        self, mock_cli_confirm: Any, mock_cli_text_input: Any
    ) -> None:
        """Test that ask_user_confirmation falls back to DEFER when reason input is cancelled."""
        mock_cli_confirm.return_value = 1  # Second option (Reject)
        mock_cli_text_input.side_effect = KeyboardInterrupt()  # User cancelled reason input

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'dangerous command'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.DEFER
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once_with('Reason (and let OpenHands know why): ')

    @patch('openhands_cli.user_actions.agent_action.cli_text_input')
    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_reject_empty_reason(
        self, mock_cli_confirm: Any, mock_cli_text_input: Any
    ) -> None:
        """Test that ask_user_confirmation handles empty reason input correctly."""
        mock_cli_confirm.return_value = 1  # Second option (Reject)
        mock_cli_text_input.return_value = '   '  # Whitespace-only reason (should be treated as empty)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'dangerous command'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.REJECT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''  # Should be empty after stripping whitespace
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once_with('Reason (and let OpenHands know why): ')

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
            monkeypatch.setattr(agent_action, 'cli_confirm', wrapper, raising=True)

            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(
                    ask_user_confirmation, [MockAction(command='echo hello world')]
                )

                _send_keys(pipe, '\x03')  # Ctrl-C (ignored)
                result = fut.result(timeout=2.0)
                assert isinstance(result, ConfirmationResult)
                assert (
                    result.decision == UserConfirmation.DEFER
                )  # escaped confirmation view
                assert result.reason == ''
                assert result.policy_change is None

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_always_accept(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation returns ACCEPT with NeverConfirm policy when user selects third option."""
        mock_cli_confirm.return_value = 2  # Third option (Always proceed)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'echo test'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.ACCEPT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert isinstance(result.policy_change, NeverConfirm)

    def test_conversation_runner_handles_always_accept(self) -> None:
        """Test that ConversationRunner disables confirmation mode when NeverConfirm policy is returned."""
        mock_conversation = MagicMock()
        mock_conversation.confirmation_policy_active = True
        mock_conversation.is_confirmation_mode_active = True
        runner = ConversationRunner(mock_conversation)

        # Enable confirmation mode first
        runner.set_confirmation_policy(AlwaysConfirm())
        assert runner.is_confirmation_mode_active is True

        # Mock get_unmatched_actions to return some actions
        with patch(
            'openhands_cli.runner.ConversationState.get_unmatched_actions'
        ) as mock_get_actions:
            mock_action = MagicMock()
            mock_action.tool_name = 'bash'
            mock_action.action = 'echo test'
            mock_get_actions.return_value = [mock_action]

            # Mock ask_user_confirmation to return ACCEPT with NeverConfirm policy
            with patch('openhands_cli.runner.ask_user_confirmation') as mock_ask:
                mock_ask.return_value = ConfirmationResult(
                    decision=UserConfirmation.ACCEPT,
                    reason='',
                    policy_change=NeverConfirm(),
                )

                # Mock print_formatted_text to avoid output during test
                with patch('openhands_cli.runner.print_formatted_text'):
                    # Mock setup_conversation to avoid real conversation creation
                    with patch('openhands_cli.runner.setup_conversation') as mock_setup:
                        # Return a new mock conversation with confirmation mode disabled
                        new_mock_conversation = MagicMock()
                        new_mock_conversation.id = mock_conversation.id
                        new_mock_conversation.is_confirmation_mode_active = False
                        mock_setup.return_value = new_mock_conversation

                        result = runner._handle_confirmation_request()

                        # Verify that confirmation mode was disabled
                        assert result == UserConfirmation.ACCEPT
                        # Should have called setup_conversation to toggle confirmation mode
                        mock_setup.assert_called_once_with(
                            mock_conversation.id, include_security_analyzer=False
                        )
                        # Should have called set_confirmation_policy with NeverConfirm on new conversation
                        new_mock_conversation.set_confirmation_policy.assert_called_with(
                            NeverConfirm()
                        )

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_auto_confirm_safe(
        self, mock_cli_confirm: Any
    ) -> None:
        """Test that ask_user_confirmation returns ACCEPT with policy_change when user selects fourth option."""
        mock_cli_confirm.return_value = (
            3  # Fourth option (Auto-confirm LOW/MEDIUM, ask for HIGH)
        )

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'echo test'

        result = ask_user_confirmation([mock_action])
        assert isinstance(result, ConfirmationResult)
        assert result.decision == UserConfirmation.ACCEPT
        assert result.reason == ''
        assert result.policy_change is not None
        assert isinstance(result.policy_change, ConfirmRisky)
        assert result.policy_change.threshold == SecurityRisk.HIGH

    def test_conversation_runner_handles_auto_confirm_safe(self) -> None:
        """Test that ConversationRunner sets ConfirmRisky policy when policy_change is provided."""
        mock_conversation = MagicMock()
        mock_conversation.confirmation_policy_active = True
        mock_conversation.is_confirmation_mode_active = True
        runner = ConversationRunner(mock_conversation)

        # Enable confirmation mode first
        runner.set_confirmation_policy(AlwaysConfirm())
        assert runner.is_confirmation_mode_active is True

        # Mock get_unmatched_actions to return some actions
        with patch(
            'openhands_cli.runner.ConversationState.get_unmatched_actions'
        ) as mock_get_actions:
            mock_action = MagicMock()
            mock_action.tool_name = 'bash'
            mock_action.action = 'echo test'
            mock_get_actions.return_value = [mock_action]

            # Mock ask_user_confirmation to return ConfirmationResult with policy_change
            with patch('openhands_cli.runner.ask_user_confirmation') as mock_ask:
                expected_policy = ConfirmRisky(threshold=SecurityRisk.HIGH)
                mock_ask.return_value = ConfirmationResult(
                    decision=UserConfirmation.ACCEPT,
                    reason='',
                    policy_change=expected_policy,
                )

                # Mock print_formatted_text to avoid output during test
                with patch('openhands_cli.runner.print_formatted_text'):
                    result = runner._handle_confirmation_request()

                    # Verify that security-based confirmation policy was set
                    assert result == UserConfirmation.ACCEPT
                    # Should set ConfirmRisky policy with HIGH threshold
                    mock_conversation.set_confirmation_policy.assert_called_with(
                        expected_policy
                    )
