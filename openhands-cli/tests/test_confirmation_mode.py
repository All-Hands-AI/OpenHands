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
        runner = ConversationRunner(mock_conversation)

        # Verify initial state
        assert runner.is_confirmation_mode_enabled is False

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

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_no(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation returns REJECT when user selects no."""
        mock_cli_confirm.return_value = 1  # Second option (No, reject)

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

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_n_shorthand(self, mock_cli_confirm: Any) -> None:
        """Test that ask_user_confirmation accepts second option as no."""
        mock_cli_confirm.return_value = 1  # Second option (No, reject)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'dangerous command'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.REJECT
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None

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
        """Test that ask_user_confirmation returns REJECT when user selects 'No (with reason)'."""
        mock_cli_confirm.return_value = 2  # Third option (No, with reason)
        mock_cli_text_input.return_value = ('This action is too risky', False)

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'rm -rf /'

        result = ask_user_confirmation([mock_action])
        assert isinstance(result, ConfirmationResult)
        assert result.decision == UserConfirmation.REJECT
        assert result.reason == 'This action is too risky'
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once()

    @patch('openhands_cli.user_actions.agent_action.cli_text_input')
    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_no_with_reason_cancelled(
        self, mock_cli_confirm: Any, mock_cli_text_input: Any
    ) -> None:
        """Test that ask_user_confirmation falls back to DEFER when reason input is cancelled."""
        mock_cli_confirm.return_value = 2  # Third option (No, with reason)
        mock_cli_text_input.return_value = ('', True)  # User cancelled reason input

        mock_action = MagicMock()
        mock_action.tool_name = 'bash'
        mock_action.action = 'dangerous command'

        result = ask_user_confirmation([mock_action])
        assert result.decision == UserConfirmation.DEFER
        assert isinstance(result, ConfirmationResult)
        assert result.reason == ''
        assert result.policy_change is None
        mock_cli_text_input.assert_called_once()

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
        """Test that ask_user_confirmation returns ACCEPT with NeverConfirm policy when user selects fourth option."""
        mock_cli_confirm.return_value = 3  # Fourth option (Always proceed)

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
        runner = ConversationRunner(mock_conversation)

        # Enable confirmation mode first
        runner.set_confirmation_policy(AlwaysConfirm())
        assert runner.is_confirmation_mode_enabled is True

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

                # Mock setup_conversation to avoid creating a real conversation
                with patch('openhands_cli.runner.setup_conversation') as mock_setup:
                    mock_setup.return_value = mock_conversation
                    
                    # Mock print_formatted_text to avoid output during test
                    with patch('openhands_cli.runner.print_formatted_text'):
                        result = runner._handle_confirmation_request()

                        # Verify that confirmation mode was disabled
                        assert result == UserConfirmation.ACCEPT
                        # Should have called set_confirmation_policy with NeverConfirm
                        mock_conversation.set_confirmation_policy.assert_called_with(
                            NeverConfirm()
                        )

    @patch('openhands_cli.user_actions.agent_action.cli_confirm')
    def test_ask_user_confirmation_auto_confirm_safe(
        self, mock_cli_confirm: Any
    ) -> None:
        """Test that ask_user_confirmation returns ACCEPT with policy_change when user selects fifth option."""
        mock_cli_confirm.return_value = (
            4  # Fifth option (Auto-confirm LOW/MEDIUM, ask for HIGH)
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
        runner = ConversationRunner(mock_conversation)

        # Enable confirmation mode first
        runner.set_confirmation_policy(AlwaysConfirm())
        assert runner.is_confirmation_mode_enabled is True

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

    def test_toggle_confirmation_mode_from_disabled_to_enabled(self) -> None:
        """Test that toggle_confirmation_mode enables confirmation mode when currently disabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        runner = ConversationRunner(mock_conversation)
        
        # Initially disabled
        assert runner.is_confirmation_mode_enabled is False
        
        # Mock setup_conversation to return a conversation with security analyzer
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_setup.return_value = mock_enabled_conversation
            
            # Toggle confirmation mode
            runner.toggle_confirmation_mode()
            
            # Verify setup_conversation was called with include_security_analyzer=True
            mock_setup.assert_called_once_with(
                mock_conversation.id,
                include_security_analyzer=True
            )
            
            # Verify conversation was updated
            assert runner.conversation == mock_enabled_conversation
            
            # Verify AlwaysConfirm policy was set
            mock_enabled_conversation.set_confirmation_policy.assert_called_once_with(
                AlwaysConfirm()
            )

    def test_toggle_confirmation_mode_from_enabled_to_disabled(self) -> None:
        """Test that toggle_confirmation_mode disables confirmation mode when currently enabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        runner = ConversationRunner(mock_conversation)
        
        # Initially enabled
        assert runner.is_confirmation_mode_enabled is True
        
        # Mock setup_conversation to return a conversation without security analyzer
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_setup.return_value = mock_disabled_conversation
            
            # Toggle confirmation mode
            runner.toggle_confirmation_mode()
            
            # Verify setup_conversation was called with include_security_analyzer=False
            mock_setup.assert_called_once_with(
                mock_conversation.id,
                include_security_analyzer=False
            )
            
            # Verify conversation was updated
            assert runner.conversation == mock_disabled_conversation
            
            # Verify NeverConfirm policy was set
            mock_disabled_conversation.set_confirmation_policy.assert_called_once_with(
                NeverConfirm()
            )

    def test_security_analyzer_exists_when_confirmation_mode_enabled(self) -> None:
        """Test that security analyzer exists when confirmation mode is enabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        runner = ConversationRunner(mock_conversation)
        
        # Confirmation mode should be enabled
        assert runner.is_confirmation_mode_enabled is True
        
        # Security analyzer should exist
        assert runner.conversation.agent.security_analyzer is not None

    def test_security_analyzer_none_when_confirmation_mode_disabled(self) -> None:
        """Test that security analyzer is None when confirmation mode is disabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        runner = ConversationRunner(mock_conversation)
        
        # Confirmation mode should be disabled
        assert runner.is_confirmation_mode_enabled is False
        
        # Security analyzer should be None
        assert runner.conversation.agent.security_analyzer is None

    def test_confirmation_policy_always_confirm_when_enabled(self) -> None:
        """Test that confirmation policy is AlwaysConfirm when confirmation mode is enabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        runner = ConversationRunner(mock_conversation)
        
        # Enable confirmation mode explicitly
        runner.set_confirmation_policy(AlwaysConfirm())
        
        # Verify AlwaysConfirm policy was set
        mock_conversation.set_confirmation_policy.assert_called_with(AlwaysConfirm())

    def test_confirmation_policy_never_confirm_when_disabled(self) -> None:
        """Test that confirmation policy is NeverConfirm when confirmation mode is disabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        runner = ConversationRunner(mock_conversation)
        
        # Disable confirmation mode explicitly
        runner.set_confirmation_policy(NeverConfirm())
        
        # Verify NeverConfirm policy was set
        mock_conversation.set_confirmation_policy.assert_called_with(NeverConfirm())

    def test_confirmation_mode_state_consistency_after_toggle(self) -> None:
        """Test that confirmation mode state is consistent after toggling."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        runner = ConversationRunner(mock_conversation)
        
        # Initially disabled
        assert runner.is_confirmation_mode_enabled is False
        
        # Mock setup_conversation for enabling
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_setup.return_value = mock_enabled_conversation
            
            # Toggle to enable
            runner.toggle_confirmation_mode()
            
            # Should be enabled now
            assert runner.is_confirmation_mode_enabled is True
            assert runner.conversation.agent.security_analyzer is not None
            
            # Mock setup_conversation for disabling
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_setup.return_value = mock_disabled_conversation
            
            # Toggle to disable
            runner.toggle_confirmation_mode()
            
            # Should be disabled now
            assert runner.is_confirmation_mode_enabled is False
            assert runner.conversation.agent.security_analyzer is None

    def test_approval_with_never_confirm_disables_confirmation_mode(self) -> None:
        """Test that approving with 'Always proceed' option disables confirmation mode."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        runner = ConversationRunner(mock_conversation)
        
        # Initially enabled
        assert runner.is_confirmation_mode_enabled is True
        
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
                
                # Mock setup_conversation to return disabled conversation
                with patch('openhands_cli.runner.setup_conversation') as mock_setup:
                    mock_disabled_conversation = MagicMock()
                    mock_disabled_conversation.agent.security_analyzer = None
                    mock_disabled_conversation.confirmation_policy_active = False
                    mock_setup.return_value = mock_disabled_conversation
                    
                    # Mock print_formatted_text to avoid output during test
                    with patch('openhands_cli.runner.print_formatted_text'):
                        result = runner._handle_confirmation_request()
                        
                        # Verify that confirmation mode was disabled
                        assert result == UserConfirmation.ACCEPT
                        
                        # Verify toggle_confirmation_mode was called (setup_conversation called)
                        mock_setup.assert_called_once_with(
                            mock_conversation.id,
                            include_security_analyzer=False
                        )
                        
                        # Verify conversation was updated to disabled state
                        assert runner.conversation == mock_disabled_conversation

    def test_approval_with_confirm_risky_keeps_security_analyzer(self) -> None:
        """Test that approving with 'Auto-confirm safe' option keeps security analyzer but changes policy."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        runner = ConversationRunner(mock_conversation)
        
        # Initially enabled
        assert runner.is_confirmation_mode_enabled is True
        
        # Mock get_unmatched_actions to return some actions
        with patch(
            'openhands_cli.runner.ConversationState.get_unmatched_actions'
        ) as mock_get_actions:
            mock_action = MagicMock()
            mock_action.tool_name = 'bash'
            mock_action.action = 'echo test'
            mock_get_actions.return_value = [mock_action]
            
            # Mock ask_user_confirmation to return ACCEPT with ConfirmRisky policy
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
                    
                    # Security analyzer should still exist
                    assert runner.conversation.agent.security_analyzer is not None
                    
                    # Should set ConfirmRisky policy
                    mock_conversation.set_confirmation_policy.assert_called_with(
                        expected_policy
                    )

    def test_multiple_confirmation_mode_toggles(self) -> None:
        """Test multiple confirmation mode toggles maintain correct state."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        original_id = "original-conversation-id"
        mock_conversation.id = original_id
        runner = ConversationRunner(mock_conversation)
        
        # Initially disabled
        assert runner.is_confirmation_mode_enabled is False
        
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            # First toggle: enable
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_enabled_conversation.id = "enabled-conversation-id"
            mock_setup.return_value = mock_enabled_conversation
            
            runner.toggle_confirmation_mode()
            assert runner.is_confirmation_mode_enabled is True
            
            # Second toggle: disable
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_disabled_conversation.id = "disabled-conversation-id"
            mock_setup.return_value = mock_disabled_conversation
            
            runner.toggle_confirmation_mode()
            assert runner.is_confirmation_mode_enabled is False
            
            # Third toggle: enable again
            mock_setup.return_value = mock_enabled_conversation
            runner.toggle_confirmation_mode()
            assert runner.is_confirmation_mode_enabled is True
            
            # Verify setup_conversation was called 3 times
            assert mock_setup.call_count == 3
            
            # Verify the first call used the original conversation ID with enable=True
            first_call = mock_setup.call_args_list[0]
            assert first_call[0][0] == original_id
            assert first_call[1]['include_security_analyzer'] is True
            
            # Verify the second call used the enabled conversation ID with enable=False
            second_call = mock_setup.call_args_list[1]
            assert second_call[0][0] == "enabled-conversation-id"
            assert second_call[1]['include_security_analyzer'] is False
            
            # Verify the third call used the disabled conversation ID with enable=True
            third_call = mock_setup.call_args_list[2]
            assert third_call[0][0] == "disabled-conversation-id"
            assert third_call[1]['include_security_analyzer'] is True

    def test_confirmation_mode_property_reflects_both_analyzer_and_policy(self) -> None:
        """Test that is_confirmation_mode_enabled property correctly reflects both security analyzer and policy state."""
        mock_conversation = MagicMock()
        runner = ConversationRunner(mock_conversation)
        
        # Case 1: No security analyzer, policy inactive
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        assert runner.is_confirmation_mode_enabled is False
        
        # Case 2: Security analyzer exists, but policy inactive
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = False
        assert runner.is_confirmation_mode_enabled is False
        
        # Case 3: No security analyzer, but policy active
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = True
        assert runner.is_confirmation_mode_enabled is False
        
        # Case 4: Both security analyzer and policy active
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        assert runner.is_confirmation_mode_enabled is True
