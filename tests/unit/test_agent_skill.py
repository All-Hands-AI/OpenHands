import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../opendevin/skills')),
)
import unittest

from agentskills import edit_file, open_file


class TestAgentSkills(unittest.TestCase):
    def setUp(self):
        # Create the a.txt file before each test
        with open('/workspace/a.txt', 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    def test_open_file(self):
        result = open_file('/workspace/a.txt')
        self.assertIsNotNone(result)
        # Add more assertions based on expected output

    def test_edit_file(self):
        # Test editing a file
        edit_file('/workspace/a.txt', start=1, end=3, content='REPLACE TEXT')
        with open('/workspace/a.txt', 'r') as file:
            lines = file.readlines()
        self.assertEqual(len(lines), 3)
        # Add more assertions based on expected output


if __name__ == '__main__':
    unittest.main()
