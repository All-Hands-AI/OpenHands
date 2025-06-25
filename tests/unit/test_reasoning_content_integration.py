"""Integration tests for reasoning content feature.

This module tests the reasoning content functionality in actions,
ensuring that reasoning content is properly preserved and displayed.
"""

from openhands.agenthub.codeact_agent.function_calling import add_reasoning_content
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.action.files import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
)
from openhands.events.action.message import MessageAction


class TestReasoningContentIntegration:
    """Test reasoning content integration across the system."""

    def test_add_reasoning_content_function(self):
        """Test that add_reasoning_content function works correctly."""
        reasoning = 'This is my reasoning for the action.'

        # Test with MessageAction
        action = MessageAction(content='test message')
        result = add_reasoning_content(action, reasoning)
        assert result.reasoning_content == reasoning

        # Test with CmdRunAction
        action = CmdRunAction(command='ls -la')
        result = add_reasoning_content(action, reasoning)
        assert result.reasoning_content == reasoning

        # Test with None reasoning content
        action = MessageAction(content='test message')
        result = add_reasoning_content(action, None)
        assert result.reasoning_content is None

        # Test with empty string reasoning content
        action = MessageAction(content='test message')
        result = add_reasoning_content(action, '')
        assert result.reasoning_content is None

    def test_reasoning_content_in_action_string_representation(self):
        """Test that reasoning content appears in action string representation."""
        reasoning = 'This is my reasoning for the action.'

        # Test MessageAction
        action = MessageAction(content='test message', reasoning_content=reasoning)
        action_str = str(action)
        assert reasoning in action_str
        assert 'REASONING:' in action_str

        # Test CmdRunAction
        action = CmdRunAction(command='ls -la', reasoning_content=reasoning)
        action_str = str(action)
        assert reasoning in action_str
        assert 'REASONING:' in action_str

    def test_action_types_have_reasoning_content_field(self):
        """Test that all relevant action types have reasoning_content field."""
        # Test that key action types have the reasoning_content field
        action_types = [
            MessageAction,
            CmdRunAction,
            IPythonRunCellAction,
            FileEditAction,
            FileReadAction,
            FileWriteAction,
        ]

        for action_type in action_types:
            # Create an instance with minimal required fields
            if action_type == MessageAction:
                action = action_type(content='test')
            elif action_type == CmdRunAction:
                action = action_type(command='test')
            elif action_type == IPythonRunCellAction:
                action = action_type(code='test')
            elif action_type == FileEditAction:
                action = action_type(path='test')
            elif action_type == FileReadAction:
                action = action_type(path='test')
            elif action_type == FileWriteAction:
                action = action_type(path='test', content='test')

            # Check that reasoning_content field exists and can be set
            assert hasattr(action, 'reasoning_content')
            action.reasoning_content = 'test reasoning'
            assert action.reasoning_content == 'test reasoning'

    def test_reasoning_content_preservation_in_actions(self):
        """Test that reasoning content is preserved when creating actions."""
        reasoning = 'I need to analyze this carefully.'

        # Test different action types
        actions = [
            MessageAction(content='test', reasoning_content=reasoning),
            CmdRunAction(command='ls', reasoning_content=reasoning),
            IPythonRunCellAction(code="print('hello')", reasoning_content=reasoning),
            FileEditAction(path='/test', reasoning_content=reasoning),
            FileReadAction(path='/test', reasoning_content=reasoning),
            FileWriteAction(path='/test', content='test', reasoning_content=reasoning),
        ]

        for action in actions:
            assert action.reasoning_content == reasoning

            # Test that it appears in string representation
            action_str = str(action)
            assert reasoning in action_str
            # Check for either "REASONING:" or "Reasoning:" (different actions use different formats)
            assert 'REASONING:' in action_str or 'Reasoning:' in action_str

    def test_reasoning_content_none_handling(self):
        """Test that None reasoning content is handled correctly."""
        actions = [
            MessageAction(content='test', reasoning_content=None),
            CmdRunAction(command='ls', reasoning_content=None),
            IPythonRunCellAction(code="print('hello')", reasoning_content=None),
        ]

        for action in actions:
            assert action.reasoning_content is None

            # Test that REASONING doesn't appear in string representation
            action_str = str(action)
            assert 'REASONING:' not in action_str
