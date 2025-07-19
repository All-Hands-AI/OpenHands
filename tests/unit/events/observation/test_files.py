"""Tests for file observation classes."""

import os
import sys
import unittest

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from openhands.events.observation.files import (
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
)


class TestFileObservations(unittest.TestCase):
    """Test the file observation classes."""

    def test_file_read_observation(self):
        """Test the FileReadObservation class."""
        obs = FileReadObservation(path='/test/file.txt', content='file content')
        self.assertEqual('I read the file /test/file.txt.', obs.message)
        self.assertEqual(
            '[Read from /test/file.txt is successful.]\nfile content', str(obs)
        )

    def test_file_write_observation(self):
        """Test the FileWriteObservation class."""
        obs = FileWriteObservation(path='/test/file.txt', content='file content')
        self.assertEqual('I wrote to the file /test/file.txt.', obs.message)
        self.assertEqual(
            '[Write to /test/file.txt is successful.]\nfile content', str(obs)
        )

    def test_file_edit_observation(self):
        """Test the FileEditObservation class."""
        # Need to provide content parameter for Observation base class
        obs = FileEditObservation(
            path='/test/file.py',
            old_content='old code',
            new_content='new code',
            content='file edit content',
        )
        # Test basic properties
        self.assertEqual('I edited the file /test/file.py.', obs.message)

        # Test _get_language_from_extension method
        self.assertEqual('python', obs._get_language_from_extension())

        # Test with different extensions
        obs.path = '/test/file.js'
        self.assertEqual('javascript', obs._get_language_from_extension())

        obs.path = '/test/file.tsx'
        self.assertEqual('tsx', obs._get_language_from_extension())

        obs.path = '/test/file.md'
        self.assertEqual('markdown', obs._get_language_from_extension())

        # Test with unknown extension
        obs.path = '/test/file.unknown'
        self.assertEqual('plaintext', obs._get_language_from_extension())

        # Test case insensitivity
        obs.path = '/test/file.PY'
        self.assertEqual('python', obs._get_language_from_extension())


if __name__ == '__main__':
    unittest.main()
