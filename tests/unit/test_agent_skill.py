import contextlib
import io
import os
import tempfile
import unittest

from opendevin.skills.agentskills import (
    create_file,
    edit_file,
    goto_line,
    open_file,
    scroll_down,
    scroll_up,
    search_dir,
)


class TestAgentSkills(unittest.TestCase):
    def test_open_file_unexist_path(self):
        with self.assertRaises(FileNotFoundError):
            open_file('/unexist/path/a.txt')

    def test_open_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
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
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
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
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path, 100)
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

    def test_create_file_unexist_path(self):
        with self.assertRaises(FileNotFoundError):
            create_file('/unexist/path/a.txt')

    def test_create_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    create_file(os.path.join(temp_dir, 'a.txt'))
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

    def test_goto_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 1001)]))

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
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

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    goto_line(100)
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

    def test_goto_line_negative(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 5)]))
            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
            with self.assertRaises(ValueError):
                goto_line(-1)

    def test_goto_line_out_of_bound(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 5)]))
            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
            with self.assertRaises(ValueError):
                goto_line(100)

    def test_scroll_down(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 1001)]))

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
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

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    scroll_down()
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = f'[File: {temp_file_path} (1000 lines total)]\n'
            # for WINDOW = 100
            for i in range(52, 152):
                expected += f'{i}: Line {i}\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_scroll_up(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 1001)]))

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path, 300)
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = f'[File: {temp_file_path} (1000 lines total)]\n'
            for i in range(251, 351):
                expected += f'{i}: Line {i}\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    scroll_up()
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = f'[File: {temp_file_path} (1000 lines total)]\n'
            # for WINDOW = 100
            for i in range(151, 251):
                expected += f'{i}: Line {i}\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_scroll_down_edge(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            with open(temp_file_path, 'w') as file:
                file.write('\n'.join([f'Line {i}' for i in range(1, 10)]))

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    open_file(temp_file_path)
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = f'[File: {temp_file_path} (9 lines total)]\n'
            for i in range(1, 10):
                expected += f'{i}: Line {i}\n'

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    scroll_down()
                result = buf.getvalue()
            self.assertIsNotNone(result)

            # expected should be unchanged
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

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    edit_file(start=1, end=3, content='REPLACE TEXT')
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

    def test_edit_file_from_scratch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            create_file(temp_file_path)
            open_file(temp_file_path)

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    edit_file(start=1, end=1, content='REPLACE TEXT')
                result = buf.getvalue()
                expected = (
                    f'[File: {temp_file_path} (1 lines total after edit)]\n'
                    '1: REPLACE TEXT\n'
                    '[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]\n'
                )
                self.assertEqual(
                    list(filter(None, result.split('\n'))),
                    list(filter(None, expected.split('\n'))),
                )

            with open(temp_file_path, 'r') as file:
                lines = file.readlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(lines[0].rstrip(), 'REPLACE TEXT')

    def test_edit_file_from_scratch_multiline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, 'a.txt')
            create_file(temp_file_path)
            open_file(temp_file_path)

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    edit_file(
                        start=1,
                        end=1,
                        content='REPLACE TEXT1\nREPLACE TEXT2\nREPLACE TEXT3',
                    )
                result = buf.getvalue()
                expected = (
                    f'[File: {temp_file_path} (3 lines total after edit)]\n'
                    '1: REPLACE TEXT1\n'
                    '2: REPLACE TEXT2\n'
                    '3: REPLACE TEXT3\n'
                    '[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]\n'
                )
                self.assertEqual(
                    list(filter(None, result.split('\n'))),
                    list(filter(None, expected.split('\n'))),
                )

            with open(temp_file_path, 'r') as file:
                lines = file.readlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0].rstrip(), 'REPLACE TEXT1')
            self.assertEqual(lines[1].rstrip(), 'REPLACE TEXT2')
            self.assertEqual(lines[2].rstrip(), 'REPLACE TEXT3')

    def test_edit_file_not_opened(self):
        with self.assertRaises(FileNotFoundError):
            edit_file(start=1, end=3, content='REPLACE TEXT')

    def test_search_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # create a file with the search term "bingo"
            for i in range(1, 101):
                temp_file_path = os.path.join(temp_dir, f'a{i}.txt')
                with open(temp_file_path, 'w') as file:
                    file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')
                    if i == 50:
                        file.write('bingo')

            # test
            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    search_dir('bingo', temp_dir)
                result = buf.getvalue()
            print(result)
            self.assertIsNotNone(result)

            expected = (
                f'[Found 1 matches for "bingo" in {temp_dir}]\n'
                f'{temp_dir}/a50.txt (Line 6): bingo\n'
                f'[End of matches for "bingo" in {temp_dir}]\n'
            )
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_search_dir_not_exist_term(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # create a file with the search term "bingo"
            for i in range(1, 101):
                temp_file_path = os.path.join(temp_dir, f'a{i}.txt')
                with open(temp_file_path, 'w') as file:
                    file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')

            # test
            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    search_dir('non-exist', temp_dir)
                result = buf.getvalue()
            print(result)
            self.assertIsNotNone(result)

            expected = f'No matches found for "non-exist" in {temp_dir}\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_search_dir_too_much_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # create a file with the search term "bingo"
            for i in range(1, 1000):
                temp_file_path = os.path.join(temp_dir, f'a{i}.txt')
                with open(temp_file_path, 'w') as file:
                    file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')

            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    search_dir('Line 5', temp_dir)
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = f'More than 999 files matched for "Line 5" in {temp_dir}. Please narrow your search.\n'
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )

    def test_search_dir_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            # create a file with the search term "bingo"
            for i in range(1, 101):
                temp_file_path = os.path.join(temp_dir, f'a{i}.txt')
                with open(temp_file_path, 'w') as file:
                    file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')
                    if i == 50:
                        file.write('bingo')

            # test
            with io.StringIO() as buf:
                with contextlib.redirect_stdout(buf):
                    search_dir('bingo')
                result = buf.getvalue()
            self.assertIsNotNone(result)

            expected = (
                '[Found 1 matches for "bingo" in ./]\n'
                './a50.txt (Line 6): bingo\n'
                '[End of matches for "bingo" in ./]\n'
            )
            self.assertEqual(
                list(filter(None, result.split('\n'))),
                list(filter(None, expected.split('\n'))),
            )


if __name__ == '__main__':
    unittest.main()
