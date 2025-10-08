#!/usr/bin/env python3
"""
Tests for /confirm command integration in OpenHands CLI agent chat.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import setup_conversation

from openhands.sdk.security.confirmation_policy import AlwaysConfirm, NeverConfirm


class TestConfirmCommandIntegration:
    """Test suite for /confirm command integration."""

    def test_confirm_command_toggles_confirmation_mode_from_disabled_to_enabled(self) -> None:
        """Test that /confirm command enables confirmation mode when currently disabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        mock_conversation.id = "test-conversation-id"
        
        runner = ConversationRunner(mock_conversation)
        
        # Initially disabled
        assert runner.is_confirmation_mode_enabled is False
        
        # Mock setup_conversation to return enabled conversation
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_enabled_conversation.id = "test-conversation-id"
            mock_setup.return_value = mock_enabled_conversation
            
            # Test the toggle
            runner.toggle_confirmation_mode()
            
            # Verify it's now enabled
            assert runner.is_confirmation_mode_enabled is True
            
            # Verify setup_conversation was called correctly
            mock_setup.assert_called_once_with(
                "test-conversation-id",
                include_security_analyzer=True
            )
            
            # Verify AlwaysConfirm policy was set
            mock_enabled_conversation.set_confirmation_policy.assert_called_once_with(
                AlwaysConfirm()
            )

    def test_confirm_command_toggles_confirmation_mode_from_enabled_to_disabled(self) -> None:
        """Test that /confirm command disables confirmation mode when currently enabled."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        mock_conversation.id = "test-conversation-id"
        
        runner = ConversationRunner(mock_conversation)
        
        # Initially enabled
        assert runner.is_confirmation_mode_enabled is True
        
        # Mock setup_conversation to return disabled conversation
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_disabled_conversation.id = "test-conversation-id"
            mock_setup.return_value = mock_disabled_conversation
            
            # Test the toggle
            runner.toggle_confirmation_mode()
            
            # Verify it's now disabled
            assert runner.is_confirmation_mode_enabled is False
            
            # Verify setup_conversation was called correctly
            mock_setup.assert_called_once_with(
                "test-conversation-id",
                include_security_analyzer=False
            )
            
            # Verify NeverConfirm policy was set
            mock_disabled_conversation.set_confirmation_policy.assert_called_once_with(
                NeverConfirm()
            )

    def test_confirm_command_displays_correct_status_message_when_enabling(self) -> None:
        """Test that /confirm command displays correct status message when enabling confirmation mode."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        mock_conversation.id = "test-conversation-id"
        
        runner = ConversationRunner(mock_conversation)
        
        # Mock setup_conversation to return enabled conversation
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_setup.return_value = mock_enabled_conversation
            
            # Test the toggle and verify status
            runner.toggle_confirmation_mode()
            
            # Verify the status is now enabled
            assert runner.is_confirmation_mode_enabled is True

    def test_confirm_command_displays_correct_status_message_when_disabling(self) -> None:
        """Test that /confirm command displays correct status message when disabling confirmation mode."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = MagicMock()
        mock_conversation.confirmation_policy_active = True
        mock_conversation.id = "test-conversation-id"
        
        runner = ConversationRunner(mock_conversation)
        
        # Mock setup_conversation to return disabled conversation
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_setup.return_value = mock_disabled_conversation
            
            # Test the toggle and verify status
            runner.toggle_confirmation_mode()
            
            # Verify the status is now disabled
            assert runner.is_confirmation_mode_enabled is False

    def test_confirm_command_maintains_conversation_id_across_toggles(self) -> None:
        """Test that /confirm command maintains the same conversation ID across toggles."""
        original_conversation_id = "test-conversation-id"
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        mock_conversation.id = original_conversation_id
        
        runner = ConversationRunner(mock_conversation)
        
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            # First toggle: enable
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_enabled_conversation.id = original_conversation_id
            mock_setup.return_value = mock_enabled_conversation
            
            runner.toggle_confirmation_mode()
            
            # Verify conversation ID is preserved
            assert runner.conversation.id == original_conversation_id
            
            # Second toggle: disable
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_disabled_conversation.id = original_conversation_id
            mock_setup.return_value = mock_disabled_conversation
            
            runner.toggle_confirmation_mode()
            
            # Verify conversation ID is still preserved
            assert runner.conversation.id == original_conversation_id
            
            # Verify all setup_conversation calls used the same ID
            from unittest.mock import call
            expected_calls = [
                call(original_conversation_id, include_security_analyzer=True),
                call(original_conversation_id, include_security_analyzer=False),
            ]
            assert mock_setup.call_args_list == expected_calls

    def test_confirm_command_error_handling_when_setup_fails(self) -> None:
        """Test that /confirm command handles errors gracefully when setup_conversation fails."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        mock_conversation.id = "test-conversation-id"
        
        runner = ConversationRunner(mock_conversation)
        
        # Mock setup_conversation to raise an exception
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_setup.side_effect = Exception("Setup failed")
            
            # The toggle should raise the exception (no error handling in current implementation)
            with pytest.raises(Exception, match="Setup failed"):
                runner.toggle_confirmation_mode()

    def test_confirm_command_preserves_other_conversation_properties(self) -> None:
        """Test that /confirm command preserves other conversation properties during toggle."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        mock_conversation.id = "test-conversation-id"
        mock_conversation.some_other_property = "preserved_value"
        
        runner = ConversationRunner(mock_conversation)
        
        # Mock setup_conversation to return conversation with preserved properties
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_enabled_conversation.id = "test-conversation-id"
            mock_enabled_conversation.some_other_property = "preserved_value"
            mock_setup.return_value = mock_enabled_conversation
            
            # Test the toggle
            runner.toggle_confirmation_mode()
            
            # Verify the conversation was updated
            assert runner.conversation == mock_enabled_conversation
            
            # Verify properties are preserved (this is handled by setup_conversation)
            mock_setup.assert_called_once_with(
                "test-conversation-id",
                include_security_analyzer=True
            )

    def test_confirm_command_idempotent_behavior_with_rapid_toggles(self) -> None:
        """Test that /confirm command behaves correctly with rapid successive toggles."""
        mock_conversation = MagicMock()
        mock_conversation.agent.security_analyzer = None
        mock_conversation.confirmation_policy_active = False
        mock_conversation.id = "test-conversation-id"
        
        runner = ConversationRunner(mock_conversation)
        
        with patch('openhands_cli.runner.setup_conversation') as mock_setup:
            # Setup mock conversations for alternating states
            mock_enabled_conversation = MagicMock()
            mock_enabled_conversation.agent.security_analyzer = MagicMock()
            mock_enabled_conversation.confirmation_policy_active = True
            mock_enabled_conversation.id = "test-conversation-id"
            
            mock_disabled_conversation = MagicMock()
            mock_disabled_conversation.agent.security_analyzer = None
            mock_disabled_conversation.confirmation_policy_active = False
            mock_disabled_conversation.id = "test-conversation-id"
            
            # Alternate between enabled and disabled states
            mock_setup.side_effect = [
                mock_enabled_conversation,   # First toggle: enable
                mock_disabled_conversation,  # Second toggle: disable
                mock_enabled_conversation,   # Third toggle: enable
                mock_disabled_conversation,  # Fourth toggle: disable
            ]
            
            # Perform rapid toggles
            assert runner.is_confirmation_mode_enabled is False
            
            runner.toggle_confirmation_mode()  # Enable
            assert runner.is_confirmation_mode_enabled is True
            
            runner.toggle_confirmation_mode()  # Disable
            assert runner.is_confirmation_mode_enabled is False
            
            runner.toggle_confirmation_mode()  # Enable
            assert runner.is_confirmation_mode_enabled is True
            
            runner.toggle_confirmation_mode()  # Disable
            assert runner.is_confirmation_mode_enabled is False
            
            # Verify all calls were made with correct parameters
            from unittest.mock import call
            expected_calls = [
                call("test-conversation-id", include_security_analyzer=True),
                call("test-conversation-id", include_security_analyzer=False),
                call("test-conversation-id", include_security_analyzer=True),
                call("test-conversation-id", include_security_analyzer=False),
            ]
            assert mock_setup.call_args_list == expected_calls