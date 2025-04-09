"""Tests for context reorganization functionality."""

import unittest
from unittest.mock import MagicMock

from openhands.events.action.agent import ContextReorganizationAction
from openhands.events.observation import FileReadObservation
from openhands.events.observation.context_reorganization import (
    ContextReorganizationObservation,
)
from openhands.runtime.base import Runtime


class TestContextReorganization(unittest.TestCase):
    """Test context reorganization functionality."""

    def test_runtime_context_reorganization(self):
        """Test that Runtime.context_reorganization correctly handles ContextReorganizationAction."""
        # Create a mock Runtime instance
        runtime = MagicMock(spec=Runtime)
        runtime.log = MagicMock()

        # Set up the mock read method to return FileReadObservation
        runtime.read.side_effect = [
            FileReadObservation(content='File 1 content', path='/test/file1.py'),
            FileReadObservation(content='File 2 content', path='/test/file2.py'),
        ]

        # Create a ContextReorganizationAction
        action = ContextReorganizationAction(
            summary='Test summary',
            files=[{'path': '/test/file1.py'}, {'path': '/test/file2.py'}],
        )

        # Call the method
        # We need to use the actual implementation, not the mock
        observation = Runtime.context_reorganization(runtime, action)

        # Check that the observation is correct
        self.assertIsInstance(observation, ContextReorganizationObservation)
        self.assertEqual(observation.summary, 'Test summary')
        self.assertEqual(len(observation.files), 2)
        self.assertIn('Test summary', observation.content)
        self.assertIn('File 1 content', observation.content)
        self.assertIn('File 2 content', observation.content)

        # Check that read was called with the correct arguments
        self.assertEqual(runtime.read.call_count, 2)


if __name__ == '__main__':
    unittest.main()
