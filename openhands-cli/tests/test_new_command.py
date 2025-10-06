"""Tests for the /new command functionality."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from openhands_cli.agent_chat import _start_fresh_conversation


class TestNewCommand:
    """Test the /new command functionality."""

    @patch('openhands_cli.agent_chat.setup_conversation')
    def test_start_fresh_conversation_success(self, mock_setup_conversation):
        """Test that _start_fresh_conversation creates a new conversation successfully."""
        # Mock the conversation object
        mock_conversation = MagicMock()
        mock_conversation.id = UUID('12345678-1234-5678-9abc-123456789abc')
        mock_setup_conversation.return_value = mock_conversation

        # Call the function
        result = _start_fresh_conversation()

        # Verify the result
        assert result == mock_conversation
        mock_setup_conversation.assert_called_once_with()

    @patch('openhands_cli.agent_chat.setup_conversation')
    def test_start_fresh_conversation_missing_agent_spec(self, mock_setup_conversation):
        """Test that _start_fresh_conversation handles MissingAgentSpec exception."""
        from openhands_cli.setup import MissingAgentSpec
        
        # Mock setup_conversation to raise MissingAgentSpec
        mock_setup_conversation.side_effect = MissingAgentSpec("Agent not found")

        # Call the function and expect it to raise the exception
        with pytest.raises(MissingAgentSpec):
            _start_fresh_conversation()

        mock_setup_conversation.assert_called_once_with()

    @patch('openhands_cli.agent_chat.setup_conversation')
    def test_start_fresh_conversation_other_exception(self, mock_setup_conversation):
        """Test that _start_fresh_conversation handles other exceptions."""
        # Mock setup_conversation to raise a generic exception
        mock_setup_conversation.side_effect = Exception("Generic error")

        # Call the function and expect it to raise the exception
        with pytest.raises(Exception, match="Generic error"):
            _start_fresh_conversation()

        mock_setup_conversation.assert_called_once_with()


class TestNewCommandIntegration:
    """Integration tests for the /new command in the chat loop."""

    @patch('openhands_cli.agent_chat.setup_conversation')
    def test_new_command_integration(self, mock_setup_conversation):
        """Test the /new command integration in the chat loop."""
        # Mock the conversation object
        mock_conversation = MagicMock()
        mock_conversation.id = UUID('12345678-1234-5678-9abc-123456789abc')
        mock_setup_conversation.return_value = mock_conversation

        # Import and test the function that would be called in the chat loop
        from openhands_cli.agent_chat import _start_fresh_conversation
        
        # Simulate the /new command logic
        conversation = _start_fresh_conversation()

        # Verify the calls
        mock_setup_conversation.assert_called_once_with()
        assert conversation == mock_conversation

    def test_new_command_in_commands_dict(self):
        """Test that /new command is properly defined in COMMANDS dictionary."""
        from openhands_cli.tui.tui import COMMANDS
        
        assert '/new' in COMMANDS
        assert COMMANDS['/new'] == 'Start a fresh conversation'

    def test_new_command_completion(self):
        """Test that /new command appears in command completion."""
        from openhands_cli.tui.tui import CommandCompleter
        from prompt_toolkit.completion import CompleteEvent
        from prompt_toolkit.document import Document
        
        completer = CommandCompleter()
        document = Document('/n')
        completions = list(completer.get_completions(document, CompleteEvent()))
        
        # Should include /new command
        completion_texts = [c.text for c in completions]
        assert '/new' in completion_texts
        
        # Test exact match
        document = Document('/new')
        completions = list(completer.get_completions(document, CompleteEvent()))
        assert len(completions) == 1
        assert completions[0].text == '/new'