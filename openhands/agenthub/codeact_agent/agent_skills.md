# Agent Skills Documentation

## File Operations

open_file(path: str, line_number: int | None = 1, context_lines: int | None = 100) -> None:
    Opens the file at the given path in the editor. IF the file is to be edited, first use `scroll_down` repeatedly to read the full file!
    If line_number is provided, the window will be moved to include that line.
    It only shows the first 100 lines by default! `context_lines` is the max number of lines to be displayed, up to 100. Use `scroll_up` and `scroll_down` to view more content up or down.
    Args:
    path: str: The path to the file to open, preferred absolute path.
    line_number: int | None = 1: The line number to move to. Defaults to 1.
    context_lines: int | None = 100: Only shows this number of lines in the context window (usually from line 1), with line_number as the center (if possible). Defaults to 100.

goto_line(line_number: int) -> None:
    Moves the window to show the specified line number.
    Args:
    line_number: int: The line number to move to.

scroll_down() -> None:
    Moves the window down by 100 lines.
    Args:
    None

scroll_up() -> None:
    Moves the window up by 100 lines.
    Args:
    None

search_dir(search_term: str, dir_path: str = './') -> None:
    Searches for search_term in all files in dir. If dir is not provided, searches in the current directory.
    Args:
    search_term: str: The term to search for.
    dir_path: str: The path to the directory to search.

search_file(search_term: str, file_path: str | None = None) -> None:
    Searches for search_term in file. If file is not provided, searches in the current open file.
    Args:
    search_term: str: The term to search for.
    file_path: str | None: The path to the file to search.

find_file(file_name: str, dir_path: str = './') -> None:
    Finds all files with the given name in the specified directory.
    Args:
    file_name: str: The name of the file to find.
    dir_path: str: The path to the directory to search.

## Parsers

parse_pdf(file_path: str) -> None:
    Parses the content of a PDF file and prints it.
    Args:
    file_path: str: The path to the file to open.

parse_docx(file_path: str) -> None:
    Parses the content of a DOCX file and prints it.
    Args:
    file_path: str: The path to the file to open.

parse_latex(file_path: str) -> None:
    Parses the content of a LaTex file and prints it.
    Args:
    file_path: str: The path to the file to open.

parse_pptx(file_path: str) -> None:
    Parses the content of a pptx file and prints it.
    Args:
    file_path: str: The path to the file to open.
