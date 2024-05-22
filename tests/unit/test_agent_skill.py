import contextlib
import io

import pytest

from opendevin.runtime.plugins.agent_skills.agentskills import (
    create_file,
    edit_file,
    find_file,
    goto_line,
    open_file,
    scroll_down,
    scroll_up,
    search_dir,
    search_file,
)


def test_open_file_unexist_path():
    with pytest.raises(FileNotFoundError):
        open_file('/unexist/path/a.txt')


def test_open_file(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = (
        f'[File: {temp_file_path} (5 lines total)]\n'
        '1: Line 1\n'
        '2: Line 2\n'
        '3: Line 3\n'
        '4: Line 4\n'
        '5: Line 5\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_open_file_with_indentation(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\n    Line 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = (
        f'[File: {temp_file_path} (5 lines total)]\n'
        '1: Line 1\n'
        '2:     Line 2\n'
        '3: Line 3\n'
        '4: Line 4\n'
        '5: Line 5\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_open_file_long(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(1, 52):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')


def test_open_file_long_with_lineno(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path), 100)
        result = buf.getvalue()
    assert result is not None
    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(51, 151):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')


def test_create_file_unexist_path():
    with pytest.raises(FileNotFoundError):
        create_file('/unexist/path/a.txt')


def test_create_file(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            create_file(str(temp_file_path))
        result = buf.getvalue()

    expected = (
        f'[File: {temp_file_path} (1 lines total)]\n'
        '1:\n'
        f'[File {temp_file_path} created.]\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_goto_line(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(1, 52):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            goto_line(100)
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(51, 151):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')


def test_goto_line_negative(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 5)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
    with pytest.raises(ValueError):
        goto_line(-1)


def test_goto_line_out_of_bound(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 5)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
    with pytest.raises(ValueError):
        goto_line(100)


def test_scroll_down(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(1, 52):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            scroll_down()
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(52, 152):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')


def test_scroll_up(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path), 300)
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(251, 351):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            scroll_up()
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(151, 251):
        expected += f'{i}: Line {i}\n'
    assert result.split('\n') == expected.split('\n')


def test_scroll_down_edge(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 10)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (9 lines total)]\n'
    for i in range(1, 10):
        expected += f'{i}: Line {i}\n'

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            scroll_down()
        result = buf.getvalue()
    assert result is not None

    # expected should be unchanged
    assert result.split('\n') == expected.split('\n')


def test_edit_file(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5'
    temp_file_path.write_text(content)

    open_file(str(temp_file_path))

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
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 3
    assert lines[0].rstrip() == 'REPLACE TEXT'
    assert lines[1].rstrip() == 'Line 4'
    assert lines[2].rstrip() == 'Line 5'


def test_edit_file_from_scratch(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    create_file(str(temp_file_path))
    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            edit_file(start=1, end=1, content='REPLACE TEXT')
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (1 lines total after edit)]\n'
            '1: REPLACE TEXT\n'
            '[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 1
    assert lines[0].rstrip() == 'REPLACE TEXT'


def test_edit_file_from_scratch_multiline(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    create_file(str(temp_file_path))
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
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 3
    assert lines[0].rstrip() == 'REPLACE TEXT1'
    assert lines[1].rstrip() == 'REPLACE TEXT2'
    assert lines[2].rstrip() == 'REPLACE TEXT3'


def test_edit_file_not_opened():
    with pytest.raises(FileNotFoundError):
        edit_file(start=1, end=3, content='REPLACE TEXT')


def test_search_dir(tmp_path):
    # create files with the search term "bingo"
    for i in range(1, 101):
        temp_file_path = tmp_path / f'a{i}.txt'
        with open(temp_file_path, 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')
            if i == 50:
                file.write('bingo')

    # test
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            search_dir('bingo', str(tmp_path))
        result = buf.getvalue()
    assert result is not None

    expected = (
        f'[Found 1 matches for "bingo" in {tmp_path}]\n'
        f'{tmp_path}/a50.txt (Line 6): bingo\n'
        f'[End of matches for "bingo" in {tmp_path}]\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_search_dir_not_exist_term(tmp_path):
    # create files with the search term "bingo"
    for i in range(1, 101):
        temp_file_path = tmp_path / f'a{i}.txt'
        with open(temp_file_path, 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')

    # test
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            search_dir('non-exist', str(tmp_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'No matches found for "non-exist" in {tmp_path}\n'
    assert result.split('\n') == expected.split('\n')


def test_search_dir_too_much_match(tmp_path):
    # create files with the search term "Line 5"
    for i in range(1, 1000):
        temp_file_path = tmp_path / f'a{i}.txt'
        with open(temp_file_path, 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            search_dir('Line 5', str(tmp_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'More than 999 files matched for "Line 5" in {tmp_path}. Please narrow your search.\n'
    assert result.split('\n') == expected.split('\n')


def test_search_dir_cwd(tmp_path, monkeypatch):
    # Using pytest's monkeypatch to change directory without affecting other tests
    monkeypatch.chdir(tmp_path)
    # create files with the search term "bingo"
    for i in range(1, 101):
        temp_file_path = tmp_path / f'a{i}.txt'
        with open(temp_file_path, 'w') as file:
            file.write('Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n')
            if i == 50:
                file.write('bingo')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            search_dir('bingo')
        result = buf.getvalue()
    assert result is not None

    expected = (
        '[Found 1 matches for "bingo" in ./]\n'
        './a50.txt (Line 6): bingo\n'
        '[End of matches for "bingo" in ./]\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_search_file(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            search_file('Line 5', str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = f'[Found 1 matches for "Line 5" in {temp_file_path}]\n'
    expected += 'Line 5: Line 5\n'
    expected += f'[End of matches for "Line 5" in {temp_file_path}]\n'
    assert result.split('\n') == expected.split('\n')


def test_search_file_not_exist_term(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            search_file('Line 6', str(temp_file_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[No matches found for "Line 6" in {temp_file_path}]\n'
    assert result.split('\n') == expected.split('\n')


def test_search_file_not_exist_file():
    with pytest.raises(FileNotFoundError):
        search_file('Line 6', '/unexist/path/a.txt')


def test_find_file(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            find_file('a.txt', str(tmp_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[Found 1 matches for "a.txt" in {tmp_path}]\n'
    expected += f'{tmp_path}/a.txt\n'
    expected += f'[End of matches for "a.txt" in {tmp_path}]\n'
    assert result.split('\n') == expected.split('\n')


def test_find_file_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            find_file('a.txt')
        result = buf.getvalue()
    assert result is not None


def test_find_file_not_exist_file():
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            find_file('unexist.txt')
        result = buf.getvalue()
    assert result is not None

    expected = '[No matches found for "unexist.txt" in ./]\n'
    assert result.split('\n') == expected.split('\n')


def test_find_file_not_exist_file_specific_path(tmp_path):
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            find_file('unexist.txt', str(tmp_path))
        result = buf.getvalue()
    assert result is not None

    expected = f'[No matches found for "unexist.txt" in {tmp_path}]\n'
    assert result.split('\n') == expected.split('\n')
