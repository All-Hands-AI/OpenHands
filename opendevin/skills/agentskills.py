"""
agentskills.py

This module provides various file manipulation skills for the OpenDevin agent.

Functions:
- open_file(path, line_number=None): Opens a file and optionally moves to a specific line.
- goto_line(line_number): Moves the window to show the specified line number.
- scroll_down(): Moves the window down by the number of lines specified in WINDOW.
- scroll_up(): Moves the window up by the number of lines specified in WINDOW.
- create_file(filename): Creates and opens a new file with the given name.
- search_dir(search_term, dir_path='./'): Searches for a term in all files in the specified directory.
- search_file(search_term, file_path=None): Searches for a term in the specified file or the currently open file.
- find_file(file_name, dir_path='./'): Finds all files with the given name in the specified directory.
- edit_file(path, start, end, content): Replaces lines in a file with the given content.
"""

import os
from typing import Optional

CURRENT_FILE = None
CURRENT_LINE = 1
WINDOW = 100


def _print_window(CURRENT_FILE, CURRENT_LINE, WINDOW, return_str=False):
    if CURRENT_FILE is None:
        raise FileNotFoundError('No file open. Use the open_file function first.')
    with open(CURRENT_FILE, 'r') as file:
        lines = file.readlines()
        start = max(0, CURRENT_LINE - WINDOW // 2)
        end = min(len(lines), CURRENT_LINE + WINDOW // 2)
        output = ''
        for i in range(start, end):
            output += f'{i + 1}: {lines[i].strip()}\n'
        output = output.rstrip()
        if return_str:
            return output
        else:
            print(output)


def _cur_file_header(CURRENT_FILE, total_lines):
    return f'[File: {os.path.abspath(CURRENT_FILE)} ({total_lines} lines total)]\n'


def open_file(path: str, line_number: Optional[int] = None):
    """
    Open a file and optionally move to a specific line.

    Args:
        path: str: The path to the file to open.
        line_number: Optional[int]: The line number to move to.

    Returns:
        str: A string representation of the file and window.
    """
    global CURRENT_FILE, CURRENT_LINE
    if not os.path.isfile(path):
        raise FileNotFoundError(f'File {path} not found')

    CURRENT_FILE = path
    assert os.path.isfile(CURRENT_FILE)
    with open(CURRENT_FILE) as file:
        total_lines = sum(1 for _ in file)

    if line_number is not None:
        if (
            not isinstance(line_number, int)
            or line_number < 1
            or line_number > total_lines
        ):
            raise ValueError(f'Line number must be between 1 and {total_lines}')
        CURRENT_LINE = line_number
    else:
        CURRENT_LINE = 1

    output = _cur_file_header(CURRENT_FILE, total_lines)
    output += _print_window(CURRENT_FILE, CURRENT_LINE, WINDOW, return_str=True)
    print(output)


def goto_line(line_number: int):
    """
    Moves the window to show the specified line number.

    Args:
        line_number: int: The line number to move to.
    """
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if CURRENT_FILE is None:
        raise FileNotFoundError('No file open. Use the open_file function first.')

    total_lines = sum(1 for _ in open(CURRENT_FILE))
    if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
        raise ValueError(f'Line number must be between 1 and {total_lines}')

    CURRENT_LINE = line_number

    output = _cur_file_header(CURRENT_FILE, total_lines)
    output += _print_window(CURRENT_FILE, CURRENT_LINE, WINDOW, return_str=True)
    print(output)


def scroll_down():
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if CURRENT_FILE is None:
        raise FileNotFoundError('No file open. Use the open_file function first.')

    total_lines = sum(1 for _ in open(CURRENT_FILE))
    CURRENT_LINE = min(CURRENT_LINE + WINDOW, total_lines)
    output = _cur_file_header(CURRENT_FILE, total_lines)
    output += _print_window(CURRENT_FILE, CURRENT_LINE, WINDOW, return_str=True)
    print(output)


def scroll_up():
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if CURRENT_FILE is None:
        raise FileNotFoundError('No file open. Use the open_file function first.')

    CURRENT_LINE = max(CURRENT_LINE - WINDOW, 1)
    total_lines = sum(1 for _ in open(CURRENT_FILE))
    output = _cur_file_header(CURRENT_FILE, total_lines)
    output += _print_window(CURRENT_FILE, CURRENT_LINE, WINDOW, return_str=True)
    print(output)


def create_file(filename):
    global CURRENT_FILE, CURRENT_LINE
    if os.path.exists(filename):
        raise FileExistsError(f"File '{filename}' already exists.")

    with open(filename, 'w') as file:
        file.write('\n')

    open_file(filename)
    print(f'[File {filename} created.]')


def search_dir(search_term: str, dir_path: str = './') -> None:
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f'Directory {dir_path} not found')

    matches = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.startswith('.'):
                continue
            file_path = os.path.join(root, file)
            with open(file_path, 'r', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if search_term in line:
                        matches.append((file_path, line_num, line.strip()))

    if not matches:
        print(f'No matches found for "{search_term}" in {dir_path}')
        return

    num_matches = len(matches)
    num_files = len(set(match[0] for match in matches))

    if num_files > 100:
        print(
            f'More than {num_files} files matched for "{search_term}" in {dir_path}. Please narrow your search.'
        )
        return

    print(f'Found {num_matches} matches for "{search_term}" in {dir_path}:')
    for file_path, line_num, line in matches:
        print(f'{file_path} (Line {line_num}): {line}')
    print(f'End of matches for "{search_term}" in {dir_path}')
    for match in matches:
        print(match)


def edit_file(start: int, end: int, content: str) -> None:
    """Edit a file.

    Args:
        start: int: The start line number. Must be greater or equal to 1.
        end: int: The end line number. Must be greater or equal to 1 AND greater than start AND less than or equal to the number of lines in the file.
        content: str: The content to replace the lines with.
    """
    global CURRENT_FILE, CURRENT_LINE, WINDOW
    if not CURRENT_FILE or not os.path.isfile(CURRENT_FILE):
        raise FileNotFoundError('No file open. Use the open_file function first.')

    with open(CURRENT_FILE, 'r') as file:
        lines = file.readlines()

    if not (1 <= start <= len(lines)):
        raise ValueError(
            f'Invalid start line number: {start}. Line numbers must be between 1 and {len(lines)} (inclusive).'
        )

    if not (1 <= end <= len(lines)):
        raise ValueError(
            f'Invalid end line number: {end}. Line numbers must be between 1 and {len(lines)} (inclusive).'
        )

    if start > end:
        raise ValueError(
            f'Invalid line range: {start}-{end}. Start must be less than or equal to end.'
        )

    new_lines = lines[: start - 1] + [content + '\n'] + lines[end:]

    # TODO: add linting from SWE-Bench

    with open(CURRENT_FILE, 'w') as file:
        file.writelines(new_lines)
    with open(CURRENT_FILE, 'r') as file:
        n_total_lines = len(file.readlines())
    # set current line to the center of the edited lines
    CURRENT_LINE = (start + end) // 2
    print(
        f'[File: {os.path.abspath(CURRENT_FILE)} ({n_total_lines} lines total after edit)]'
    )
    _print_window(CURRENT_FILE, CURRENT_LINE, WINDOW)
    print(
        '[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]'
    )


def search_file(search_term: str, file_path: Optional[str] = None):
    global CURRENT_FILE
    if file_path is None:
        file_path = CURRENT_FILE
    if file_path is None:
        raise FileNotFoundError(
            'No file specified or open. Use the open_file function first.'
        )
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f'File {file_path} not found')

    matches = []
    with open(file_path, 'r') as file:
        for i, line in enumerate(file, 1):
            if search_term in line:
                matches.append((i, line.strip()))

    if matches:
        print(f"Found {len(matches)} matches for '{search_term}' in {file_path}:")
        for match in matches:
            print(f'Line {match[0]}: {match[1]}')
    else:
        print(f"No matches found for '{search_term}' in {file_path}")


def find_file(file_name, dir_path='./'):
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f'Directory {dir_path} not found')

    matches = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file_name in file:
                matches.append(os.path.join(root, file))

    if matches:
        output = f"Found {len(matches)} matches for '{file_name}' in {dir_path}:\n"
        for match in matches:
            output += f'{match}\n'
        return output
    else:
        return f"No matches found for '{file_name}' in {dir_path}"
