import io
import os
import sys
import tempfile
import unittest

from opendevin.skills.agentskills import create_file, edit_file, open_file


class TestAgentSkills(unittest.TestCase):
    def test_open_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

            with io.StringIO() as buf:
                sys.stdout = buf
                open_file(temp_file_path)
                sys.stdout = sys.__stdout__
                result = buf.getvalue()
            self.assertIsNotNone(result)
            expected = (
                f'[File: {temp_file_path} (5 lines total)]\n'
                '1: Line 1\n'
                '2: Line 2\n'
                '3: Line 3\n'
                '4: Line 4\n'
                '5: Line 5\n'
            )
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_open_file_long(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 1001)]))

            with io.StringIO() as buf:
                sys.stdout = buf
                open_file(temp_file_path)
                sys.stdout = sys.__stdout__
                result = buf.getvalue()
            self.assertIsNotNone(result)
            expected = f'[File: {temp_file_path} (1000 lines total)]\n'
            # for WINDOW = 100
            for i in range(1, 52):
                expected += f'{i}: Line {i}\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_open_file_long_with_lineno(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 1001)]))

            with io.StringIO() as buf:
                sys.stdout = buf
                open_file(temp_file_path, 100)
                sys.stdout = sys.__stdout__
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = f'[File: {temp_file_path} (1000 lines total)]\n'
            # for WINDOW = 100
            for i in range(51, 151):
                expected += f'{i}: Line {i}\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_create_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with io.StringIO() as buf:
                sys.stdout = buf
                create_file(os.path.join(temp_dir, 'a.txt'))
                sys.stdout = sys.__stdout__
                result = buf.getvalue()

                expected = (
                    f'[File: {os.path.join(temp_dir, "a.txt")} (1 lines total)]\n'
                    '1:\n'
                    f'[File {os.path.join(temp_dir, "a.txt")} created.]\n'
                )
                self.assertEqual(
                    list(filter(None, result.split('\n'))),
                    list(filter(None, expected.split('\n'))),
                )

    def test_edit_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

            open_file(temp_file_path)

            # Test editing a file
            # capture stdout
            with io.StringIO() as buf:
                sys.stdout = buf
                edit_file(start=1, end=3, content='REPLACE TEXT')
                sys.stdout = sys.__stdout__
                result = buf.getvalue()
                expected = (
                    f'[File: {temp_file_path} (3 lines total after edit)]\n'
                    '1: REPLACE TEXT\n'
                    '2: Line 4\n'
                    '3: Line 5\n'
                    '[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]\n'
                )
                self.assertEqual(
                    list(filter(None, result.split('\n'))),
                    list(filter(None, expected.split('\n'))),
                )

            with open(temp_file_path, 'r') as file:
                lines = file.readlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0].rstrip(), 'REPLACE TEXT')
            self.assertEqual(lines[1].rstrip(), 'Line 4')
            self.assertEqual(lines[2].rstrip(), 'Line 5')
            # Add more assertions based on expected output

    def test_edit_file_not_opened(self):
        with self.assertRaises(FileNotFoundError):
            edit_file(start=1, end=3, content='REPLACE TEXT')


if __name__ == '__main__':
    unittest.main()
