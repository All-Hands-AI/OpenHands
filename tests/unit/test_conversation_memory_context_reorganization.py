"""Tests for conversation memory context reorganization."""

import unittest
from unittest.mock import MagicMock

from openhands.events.observation.context_reorganization import (
    ContextReorganizationObservation,
)
from openhands.memory.conversation_memory import ConversationMemory


class TestConversationMemoryContextReorganization(unittest.TestCase):
    """Test conversation memory context reorganization."""

    def test_process_observation_with_context_reorganization(self):
        """Test that _process_observation correctly handles ContextReorganizationObservation."""
        # Create a mock ConversationMemory instance
        memory = MagicMock(spec=ConversationMemory)
        memory.agent_config = MagicMock()
        memory.agent_config.max_message_chars = 10000

        # Create a ContextReorganizationObservation
        observation = ContextReorganizationObservation(
            content='Test content with file contents',
            summary='Test summary',
            files=[
                {'path': '/test/file1.py', 'view_range': [1, 10]},
                {'path': '/test/file2.py'},
            ],
        )

        # Call the method
        messages = ConversationMemory._process_observation(
            memory,
            obs=observation,
            max_message_chars=10000,
            tool_call_id_to_message={},
            vision_is_active=False,
            enable_som_visual_browsing=False,
            current_index=0,
            events=[],
        )

        # Check that we got a list with one message
        self.assertEqual(len(messages), 1)
        message = messages[0]

        # Check that the message is correct
        self.assertEqual(message.role, 'user')
        self.assertEqual(len(message.content), 1)

        # Check the content of the message
        text_content = message.content[0].text
        self.assertIn('CONTEXT REORGANIZATION:', text_content)
        self.assertIn('Summary: Test summary', text_content)
        self.assertIn('Files included in context:', text_content)
        self.assertIn('File: /test/file1.py (lines 1-10)', text_content)
        self.assertIn('File: /test/file2.py', text_content)
        self.assertIn('Test content with file contents', text_content)

    def test_process_observation_with_context_reorganization_no_file_content(self):
        """Test that _process_observation correctly handles ContextReorganizationObservation with no file content."""
        # Create a mock ConversationMemory instance
        memory = MagicMock(spec=ConversationMemory)
        memory.agent_config = MagicMock()
        memory.agent_config.max_message_chars = 10000

        # Create a ContextReorganizationObservation with no file content
        observation = ContextReorganizationObservation(
            content='Test summary',  # Content is the same as summary, indicating no file content
            summary='Test summary',
            files=[
                {'path': '/test/file1.py', 'view_range': [1, 10]},
                {'path': '/test/file2.py'},
            ],
        )

        # Call the method
        messages = ConversationMemory._process_observation(
            memory,
            obs=observation,
            max_message_chars=10000,
            tool_call_id_to_message={},
            vision_is_active=False,
            enable_som_visual_browsing=False,
            current_index=0,
            events=[],
        )

        # Check that we got a list with one message
        self.assertEqual(len(messages), 1)
        message = messages[0]

        # Check that the message is correct
        self.assertEqual(message.role, 'user')
        self.assertEqual(len(message.content), 1)

        # Check the content of the message
        text_content = message.content[0].text
        self.assertIn('CONTEXT REORGANIZATION:', text_content)
        self.assertIn('Summary: Test summary', text_content)
        self.assertIn('Files included in context:', text_content)
        self.assertIn('File: /test/file1.py (lines 1-10)', text_content)
        self.assertIn('File: /test/file2.py', text_content)
        self.assertIn('Note: File contents could not be retrieved', text_content)


if __name__ == '__main__':
    unittest.main()
