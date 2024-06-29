import contextlib
import io
import sys

import docx
import pytest

from opendevin.runtime.plugins.agent_skills.agentskills import (
    MSG_FILE_UPDATED,
    _print_window,
    create_file,
    edit_file,
    find_file,
    goto_line,
    insert_content_at_line,
    open_file,
    parse_docx,
    parse_latex,
    parse_pdf,
    parse_pptx,
    scroll_down,
    scroll_up,
    search_dir,
    search_file,
)


# CURRENT_FILE must be reset for each test
@pytest.fixture(autouse=True)
def reset_current_file():
    from opendevin.runtime.plugins.agent_skills import agentskills

    agentskills.CURRENT_FILE = None


def _numbered_test_lines(start, end) -> str:
    return ('\n'.join(f'{i}|' for i in range(start, end + 1))) + '\n'


def _generate_test_file_with_lines(temp_path, num_lines) -> str:
    file_path = temp_path / 'test_file.py'
    file_path.write_text('\n' * num_lines)
    return file_path


def test_open_file_unexist_path():
    with pytest.raises(FileNotFoundError):
        open_file('/unexist/path/a.txt')


def test_open_file(tmp_path):
    assert tmp_path is not None
    temp_file_path = tmp_path / 'a.txt'
    temp_file_path.write_text('Line 1\nLine 2\nLine 3\nLine 4\nLine 5')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path))
        result = buf.getvalue()
    assert result is not None
    expected = (
        f'[File: {temp_file_path} (5 lines total)]\n'
        '1|Line 1\n'
        '2|Line 2\n'
        '3|Line 3\n'
        '4|Line 4\n'
        '5|Line 5\n'
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
        '1|Line 1\n'
        '2|    Line 2\n'
        '3|Line 3\n'
        '4|Line 4\n'
        '5|Line 5\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_open_file_long(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = '\n'.join([f'Line {i}' for i in range(1, 1001)])
    temp_file_path.write_text(content)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(temp_file_path), 1, 50)
        result = buf.getvalue()
    assert result is not None
    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    for i in range(1, 51):
        expected += f'{i}|Line {i}\n'
    expected += '(950 more lines below)\n'
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
    expected += '(49 more lines above)\n'
    for i in range(50, 151):
        expected += f'{i}|Line {i}\n'
    expected += '(850 more lines below)\n'
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
        '1|\n'
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
    for i in range(1, 101):
        expected += f'{i}|Line {i}\n'
    expected += '(900 more lines below)\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            goto_line(100)
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    expected += '(49 more lines above)\n'
    for i in range(50, 151):
        expected += f'{i}|Line {i}\n'
    expected += '(850 more lines below)\n'
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
    for i in range(1, 101):
        expected += f'{i}|Line {i}\n'
    expected += '(900 more lines below)\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            scroll_down()
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    expected += '(50 more lines above)\n'
    for i in range(51, 152):
        expected += f'{i}|Line {i}\n'
    expected += '(849 more lines below)\n'
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
    expected += '(249 more lines above)\n'
    for i in range(250, 351):
        expected += f'{i}|Line {i}\n'
    expected += '(650 more lines below)\n'
    assert result.split('\n') == expected.split('\n')

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            scroll_up()
        result = buf.getvalue()
    assert result is not None

    expected = f'[File: {temp_file_path} (1000 lines total)]\n'
    expected += '(149 more lines above)\n'
    for i in range(150, 251):
        expected += f'{i}|Line {i}\n'
    expected += '(750 more lines below)\n'
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
        expected += f'{i}|Line {i}\n'

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            scroll_down()
        result = buf.getvalue()
    assert result is not None

    # expected should be unchanged
    assert result.split('\n') == expected.split('\n')


def test_print_window_internal(tmp_path):
    test_file_path = tmp_path / 'a.txt'
    create_file(str(test_file_path))
    open_file(str(test_file_path))
    with open(test_file_path, 'w') as file:
        for i in range(1, 101):
            file.write(f'Line `{i}`\n')

    # Define the parameters for the test
    current_line = 50
    window = 2

    # Test _print_window especially with backticks
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            _print_window(str(test_file_path), current_line, window, return_str=False)
        result = buf.getvalue()
        expected = (
            '(48 more lines above)\n'
            '49|Line `49`\n'
            '50|Line `50`\n'
            '51|Line `51`\n'
            '(49 more lines below)\n'
        )
        assert result == expected


def test_edit_file_window(tmp_path, monkeypatch):
    # Set environment variable via monkeypatch does NOT work!
    monkeypatch.setattr(
        'opendevin.runtime.plugins.agent_skills.agentskills.ENABLE_AUTO_LINT', True
    )

    content = """def any_int(a, b, c):
    return isinstance(a, int) and isinstance(b, int) and isinstance(c, int)

def test_any_int():
    assert any_int(1, 2, 3) == True
    assert any_int(1.5, 2, 3) == False
    assert any_int(1, 2.5, 3) == False
    assert any_int(1, 2, 3.5) == False
    assert any_int(1.0, 2, 3) == False
    assert any_int(1, 2.0, 3) == False
    assert any_int(1, 2, 3.0) == False
    assert any_int(0, 0, 0) == True
    assert any_int(-1, -2, -3) == True
    assert any_int(1, -2, 3) == True
    assert any_int(1.5, -2, 3) == False
    assert any_int(1, -2.5, 3) == False

def check(any_int):
    # Check some simple cases
    assert any_int(2, 3, 1)==True, "This prints if this assert fails 1 (good for debugging!)"
    assert any_int(2.5, 2, 3)==False, "This prints if this assert fails 2 (good for debugging!)"
    assert any_int(1.5, 5, 3.5)==False, "This prints if this assert fails 3 (good for debugging!)"
    assert any_int(2, 6, 2)==False, "This prints if this assert fails 4 (good for debugging!)"
    assert any_int(4, 2, 2)==True, "This prints if this assert fails 5 (good for debugging!)"
    assert any_int(2.2, 2.2, 2.2)==False, "This prints if this assert fails 6 (good for debugging!)"
    assert any_int(-4, 6, 2)==True, "This prints if this assert fails 7 (good for debugging!)"

    # Check some edge cases that are easy to work out by hand.
    assert any_int(2,1,1)==True, "This prints if this assert fails 8 (also good for debugging!)"
    assert any_int(3,4,7)==True, "This prints if this assert fails 9 (also good for debugging!)"
    assert any_int(3.0,4,7)==False, "This prints if this assert fails 10 (also good for debugging!)"

check(any_int)"""

    temp_file_path = tmp_path / 'error-test.py'
    temp_file_path.write_text(content)

    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            edit_file(
                str(temp_file_path),
                to_replace='    assert any_int(1.0, 2, 3) == False',
                new_content='        assert any_int(1.0, 2, 3) == False',
            )
        result = buf.getvalue()
        expected = (
            '[Your proposed edit has introduced new syntax error(s). Please understand the errors and retry your edit command.]\n'
            'ERRORS:\n'
            + str(temp_file_path)
            + ':9:9: '
            + 'E999 IndentationError: unexpected indent\n'
            '[This is how your edit would have looked if applied]\n'
            '-------------------------------------------------\n'
            '(3 more lines above)\n'
            '4|def test_any_int():\n'
            '5|    assert any_int(1, 2, 3) == True\n'
            '6|    assert any_int(1.5, 2, 3) == False\n'
            '7|    assert any_int(1, 2.5, 3) == False\n'
            '8|    assert any_int(1, 2, 3.5) == False\n'
            '9|        assert any_int(1.0, 2, 3) == False\n'
            '10|    assert any_int(1, 2.0, 3) == False\n'
            '11|    assert any_int(1, 2, 3.0) == False\n'
            '12|    assert any_int(0, 0, 0) == True\n'
            '13|    assert any_int(-1, -2, -3) == True\n'
            '14|    assert any_int(1, -2, 3) == True\n'
            '(19 more lines below)\n'
            '-------------------------------------------------\n'
            '\n'
            '[This is the original code before your edit]\n'
            '-------------------------------------------------\n'
            '(3 more lines above)\n'
            '4|def test_any_int():\n'
            '5|    assert any_int(1, 2, 3) == True\n'
            '6|    assert any_int(1.5, 2, 3) == False\n'
            '7|    assert any_int(1, 2.5, 3) == False\n'
            '8|    assert any_int(1, 2, 3.5) == False\n'
            '9|    assert any_int(1.0, 2, 3) == False\n'
            '10|    assert any_int(1, 2.0, 3) == False\n'
            '11|    assert any_int(1, 2, 3.0) == False\n'
            '12|    assert any_int(0, 0, 0) == True\n'
            '13|    assert any_int(-1, -2, -3) == True\n'
            '14|    assert any_int(1, -2, 3) == True\n'
            '(19 more lines below)\n'
            '-------------------------------------------------\n'
            'Your changes have NOT been applied. Please fix your edit command and try again.\n'
            'You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.\n'
            'DO NOT re-run the same failed edit command. Running it again will lead to the same error.\n'
        )
        assert result == expected


def test_edit_file(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5'
    temp_file_path.write_text(content)

    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            edit_file(
                file_name=str(temp_file_path),
                to_replace='Line 1\nLine 2\nLine 3',
                new_content='REPLACE TEXT',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (3 lines total after edit)]\n'
            '1|REPLACE TEXT\n'
            '2|Line 4\n'
            '3|Line 5\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 3
    assert lines[0].rstrip() == 'REPLACE TEXT'
    assert lines[1].rstrip() == 'Line 4'
    assert lines[2].rstrip() == 'Line 5'


def test_edit_file_sameline(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = 'Line 1\nLine 2\nLine 2\nLine 4\nLine 5'
    temp_file_path.write_text(content)

    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            edit_file(
                file_name=str(temp_file_path),
                to_replace='Line 2\nLine 2',
                new_content='Line 2\nREPLACE TEXT',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (5 lines total after edit)]\n'
            '1|Line 1\n'
            '2|Line 2\n'
            '3|REPLACE TEXT\n'
            '4|Line 4\n'
            '5|Line 5\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 5
    assert lines[0].rstrip() == 'Line 1'
    assert lines[1].rstrip() == 'Line 2'
    assert lines[2].rstrip() == 'REPLACE TEXT'
    assert lines[3].rstrip() == 'Line 4'
    assert lines[4].rstrip() == 'Line 5'


def test_edit_file_multiline(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    content = 'Line 1\nLine 2\nLine 2\nLine 4\nLine 5'
    temp_file_path.write_text(content)

    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            edit_file(
                file_name=str(temp_file_path),
                to_replace='Line 2',
                new_content='REPLACE TEXT',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (5 lines total after edit)]\n'
            '1|Line 1\n'
            '2|REPLACE TEXT\n'
            '3|Line 2\n'
            '4|Line 4\n'
            '5|Line 5\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 5
    assert lines[0].rstrip() == 'Line 1'
    assert lines[1].rstrip() == 'REPLACE TEXT'
    assert lines[2].rstrip() == 'Line 2'
    assert lines[3].rstrip() == 'Line 4'
    assert lines[4].rstrip() == 'Line 5'


def test_edit_file_toreplace_empty():
    with pytest.raises(ValueError):
        edit_file(
            str('unknown file'),
            '',
            'REPLACE TEXT',
        )


def test_insert_content_at_line(tmp_path):
    temp_file_path = tmp_path / 'b.txt'
    content = 'Line 1\nLine 2\nLine 3'
    temp_file_path.write_text(content)
    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            insert_content_at_line(
                file_name=str(temp_file_path),
                line_number=2,
                content='Inserted Line',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (4 lines total after edit)]\n'
            '1|Line 1\n'
            '2|Inserted Line\n'
            '3|Line 2\n'
            '4|Line 3\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 4
    assert lines[0].rstrip() == 'Line 1'
    assert lines[1].rstrip() == 'Inserted Line'
    assert lines[2].rstrip() == 'Line 2'
    assert lines[3].rstrip() == 'Line 3'


def test_insert_content_at_line_from_scratch(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    create_file(str(temp_file_path))
    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            insert_content_at_line(
                file_name=str(temp_file_path),
                line_number=1,
                content='REPLACE TEXT',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (2 lines total after edit)]\n'
            '1|REPLACE TEXT\n'
            '2|\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 2
    assert lines[0].rstrip() == 'REPLACE TEXT'
    assert lines[1].rstrip() == ''


def test_insert_content_at_line_from_scratch_emptyfile(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    with open(temp_file_path, 'w') as file:
        file.write('')
    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            insert_content_at_line(
                file_name=str(temp_file_path),
                line_number=1,
                content='REPLACE TEXT',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (1 lines total after edit)]\n'
            '1|REPLACE TEXT\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 1
    assert lines[0].rstrip() == 'REPLACE TEXT'


def test_insert_content_at_line_emptyline(tmp_path):
    temp_file_path = tmp_path / 'b.txt'
    content = 'Line 1\n\n'
    temp_file_path.write_text(content)
    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            insert_content_at_line(
                file_name=str(temp_file_path),
                line_number=2,
                content='Inserted Line',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (3 lines total after edit)]\n'
            '1|Line 1\n'
            '2|Inserted Line\n'
            '3|\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 3
    assert lines[0].rstrip() == 'Line 1'
    assert lines[1].rstrip() == 'Inserted Line'
    assert lines[2].rstrip() == ''


def test_insert_content_at_line_from_scratch_multiline_with_backticks_and_second_edit(
    tmp_path,
):
    temp_file_path = tmp_path / 'a.txt'
    create_file(str(temp_file_path))
    open_file(str(temp_file_path))

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            insert_content_at_line(
                str(temp_file_path),
                1,
                '`REPLACE TEXT1`\n`REPLACE TEXT2`\n`REPLACE TEXT3`',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (4 lines total after edit)]\n'
            '1|`REPLACE TEXT1`\n'
            '2|`REPLACE TEXT2`\n'
            '3|`REPLACE TEXT3`\n'
            '4|\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 4
    assert lines[0].rstrip() == '`REPLACE TEXT1`'
    assert lines[1].rstrip() == '`REPLACE TEXT2`'
    assert lines[2].rstrip() == '`REPLACE TEXT3`'
    assert lines[3].rstrip() == ''

    # Check that no backticks are escaped in the edit_file call
    assert '\\`' not in result

    # Perform a second edit
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            edit_file(
                str(temp_file_path),
                '`REPLACE TEXT1`\n`REPLACE TEXT2`\n`REPLACE TEXT3`',
                '`REPLACED TEXT1`\n`REPLACED TEXT2`\n`REPLACED TEXT3`',
            )
        second_result = buf.getvalue()
        second_expected = (
            f'[File: {temp_file_path} (4 lines total after edit)]\n'
            '1|`REPLACED TEXT1`\n'
            '2|`REPLACED TEXT2`\n'
            '3|`REPLACED TEXT3`\n'
            '4|\n' + MSG_FILE_UPDATED + '\n'
        )
        assert second_result.split('\n') == second_expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 4
    assert lines[0].rstrip() == '`REPLACED TEXT1`'
    assert lines[1].rstrip() == '`REPLACED TEXT2`'
    assert lines[2].rstrip() == '`REPLACED TEXT3`'
    assert lines[3].rstrip() == ''

    # Check that no backticks are escaped in the second edit_file call
    assert '\\`' not in second_result


def test_insert_content_at_line_from_scratch_multiline(tmp_path):
    temp_file_path = tmp_path / 'a.txt'
    create_file(str(temp_file_path))
    open_file(temp_file_path)

    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            insert_content_at_line(
                str(temp_file_path),
                1,
                content='REPLACE TEXT1\nREPLACE TEXT2\nREPLACE TEXT3',
            )
        result = buf.getvalue()
        expected = (
            f'[File: {temp_file_path} (4 lines total after edit)]\n'
            '1|REPLACE TEXT1\n'
            '2|REPLACE TEXT2\n'
            '3|REPLACE TEXT3\n'
            '4|\n' + MSG_FILE_UPDATED + '\n'
        )
        assert result.split('\n') == expected.split('\n')

    with open(temp_file_path, 'r') as file:
        lines = file.readlines()
    assert len(lines) == 4
    assert lines[0].rstrip() == 'REPLACE TEXT1'
    assert lines[1].rstrip() == 'REPLACE TEXT2'
    assert lines[2].rstrip() == 'REPLACE TEXT3'
    assert lines[3].rstrip() == ''


def test_insert_content_at_line_not_opened():
    with pytest.raises(FileNotFoundError):
        insert_content_at_line(
            str('unknown file'),
            1,
            'REPLACE TEXT',
        )


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


def test_edit_lint_file_pass(tmp_path, monkeypatch):
    # Enable linting
    monkeypatch.setattr(
        'opendevin.runtime.plugins.agent_skills.agentskills.ENABLE_AUTO_LINT', True
    )

    file_path = _generate_test_file_with_lines(tmp_path, 1)

    # Test linting functionality
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            open_file(str(file_path))
            insert_content_at_line(str(file_path), 1, "print('hello')\n")
        result = buf.getvalue()
    assert result is not None
    expected = (
        f'[File: {file_path} (1 lines total)]\n'
        '1|\n'
        f'[File: {file_path} (2 lines total after edit)]\n'
        "1|print('hello')\n"
        '2|\n' + MSG_FILE_UPDATED + '\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_lint_file_fail_undefined_name(tmp_path, monkeypatch, capsys):
    # Enable linting
    monkeypatch.setattr(
        'opendevin.runtime.plugins.agent_skills.agentskills.ENABLE_AUTO_LINT', True
    )

    current_line = 1

    file_path = _generate_test_file_with_lines(tmp_path, 1)

    open_file(str(file_path), current_line)
    insert_content_at_line(str(file_path), 1, 'undefined_name()\n')

    result = capsys.readouterr().out
    assert result is not None

    expected = (
        f'[File: {file_path} (1 lines total)]\n'
        '1|\n'
        '[Your proposed edit has introduced new syntax error(s). Please understand the errors and retry your edit command.]\n'
        'ERRORS:\n'
        f"{file_path}:1:1: F821 undefined name 'undefined_name'\n"
        '[This is how your edit would have looked if applied]\n'
        '-------------------------------------------------\n'
        '1|undefined_name()\n'
        '2|\n'
        '-------------------------------------------------\n\n'
        '[This is the original code before your edit]\n'
        '-------------------------------------------------\n'
        '1|\n'
        '-------------------------------------------------\n'
        'Your changes have NOT been applied. Please fix your edit command and try again.\n'
        'You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.\n'
        'DO NOT re-run the same failed edit command. Running it again will lead to the same error.\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_lint_file_fail_undefined_name_long(tmp_path, monkeypatch, capsys):
    # Enable linting
    monkeypatch.setattr(
        'opendevin.runtime.plugins.agent_skills.agentskills.ENABLE_AUTO_LINT', True
    )

    num_lines = 1000
    error_line = 500
    window = 100

    file_path = _generate_test_file_with_lines(tmp_path, num_lines)

    error_message = f"{file_path}:{error_line}:1: F821 undefined name 'undefined_name'"

    open_file(str(file_path))
    insert_content_at_line(str(file_path), error_line, 'undefined_name()\n')

    result = capsys.readouterr().out
    assert result is not None

    open_lines = '\n'.join([f'{i}|' for i in range(1, window + 1)])
    expected = (
        f'[File: {file_path} ({num_lines} lines total)]\n'
        f'{open_lines}\n'
        '(900 more lines below)\n'
        '[Your proposed edit has introduced new syntax error(s). Please understand the errors and retry your edit command.]\n'
        f'ERRORS:\n{error_message}\n'
        '[This is how your edit would have looked if applied]\n'
        '-------------------------------------------------\n'
        '(494 more lines above)\n'
        + _numbered_test_lines(error_line - 5, error_line - 1)
        + '500|undefined_name()\n'
        + _numbered_test_lines(error_line + 1, error_line + 5)
        + '(496 more lines below)\n'
        + '-------------------------------------------------\n\n'
        '[This is the original code before your edit]\n'
        '-------------------------------------------------\n'
        '(494 more lines above)\n'
        + _numbered_test_lines(error_line - 5, error_line + 5)
        + '(495 more lines below)\n'
        + '-------------------------------------------------\n'
        'Your changes have NOT been applied. Please fix your edit command and try again.\n'
        'You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.\n'
        'DO NOT re-run the same failed edit command. Running it again will lead to the same error.\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_lint_file_disabled_undefined_name(tmp_path, monkeypatch, capsys):
    # Disable linting
    monkeypatch.setattr(
        'opendevin.runtime.plugins.agent_skills.agentskills.ENABLE_AUTO_LINT', False
    )

    file_path = _generate_test_file_with_lines(tmp_path, 1)

    open_file(str(file_path))
    insert_content_at_line(str(file_path), 1, 'undefined_name()\n')

    result = capsys.readouterr().out
    assert result is not None
    expected = (
        f'[File: {file_path} (1 lines total)]\n'
        '1|\n'
        f'[File: {file_path} (2 lines total after edit)]\n'
        '1|undefined_name()\n'
        '2|\n' + MSG_FILE_UPDATED + '\n'
    )
    assert result.split('\n') == expected.split('\n')


def test_parse_docx(tmp_path):
    # Create a DOCX file with some content
    test_docx_path = tmp_path / 'test.docx'
    doc = docx.Document()
    doc.add_paragraph('Hello, this is a test document.')
    doc.add_paragraph('This is the second paragraph.')
    doc.save(str(test_docx_path))

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Call the parse_docx function
    parse_docx(str(test_docx_path))

    # Capture the output
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    # Check if the output is correct
    expected_output = (
        f'[Reading DOCX file from {test_docx_path}]\n'
        '@@ Page 1 @@\nHello, this is a test document.\n\n'
        '@@ Page 2 @@\nThis is the second paragraph.\n\n\n'
    )
    assert output == expected_output, f'Expected output does not match. Got: {output}'


def test_parse_latex(tmp_path):
    # Create a LaTeX file with some content
    test_latex_path = tmp_path / 'test.tex'
    with open(test_latex_path, 'w') as f:
        f.write(r"""
        \documentclass{article}
        \begin{document}
        Hello, this is a test LaTeX document.
        \end{document}
        """)

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Call the parse_latex function
    parse_latex(str(test_latex_path))

    # Capture the output
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    # Check if the output is correct
    expected_output = (
        f'[Reading LaTex file from {test_latex_path}]\n'
        'Hello, this is a test LaTeX document.\n'
    )
    assert output == expected_output, f'Expected output does not match. Got: {output}'


def test_parse_pdf(tmp_path):
    # Create a PDF file with some content
    test_pdf_path = tmp_path / 'test.pdf'
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(test_pdf_path), pagesize=letter)
    c.drawString(100, 750, 'Hello, this is a test PDF document.')
    c.save()

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Call the parse_pdf function
    parse_pdf(str(test_pdf_path))

    # Capture the output
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    # Check if the output is correct
    expected_output = (
        f'[Reading PDF file from {test_pdf_path}]\n'
        '@@ Page 1 @@\n'
        'Hello, this is a test PDF document.\n'
    )
    assert output == expected_output, f'Expected output does not match. Got: {output}'


def test_parse_pptx(tmp_path):
    test_pptx_path = tmp_path / 'test.pptx'
    from pptx import Presentation

    pres = Presentation()

    slide1 = pres.slides.add_slide(pres.slide_layouts[0])
    title1 = slide1.shapes.title
    title1.text = 'Hello, this is the first test PPTX slide.'

    slide2 = pres.slides.add_slide(pres.slide_layouts[0])
    title2 = slide2.shapes.title
    title2.text = 'Hello, this is the second test PPTX slide.'

    pres.save(str(test_pptx_path))

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    parse_pptx(str(test_pptx_path))

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    expected_output = (
        f'[Reading PowerPoint file from {test_pptx_path}]\n'
        '@@ Slide 1 @@\n'
        'Hello, this is the first test PPTX slide.\n\n'
        '@@ Slide 2 @@\n'
        'Hello, this is the second test PPTX slide.\n\n'
    )
    assert output == expected_output, f'Expected output does not match. Got: {output}'
