import argparse
import sys


def read_input(cli_multiline_input: bool = False) -> str:
    """Read input from user based on config settings."""
    if cli_multiline_input:
        print('Enter your message (enter "/exit" on a new line to finish):')
        lines = []
        while True:
            line = input('>> ').rstrip()
            if line == '/exit':  # finish input
                break
            lines.append(line)
        return '\n'.join(lines)
    else:
        return input('>> ').rstrip()


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file.

    Args:
        file_path: Path to the file to read

    Returns:
        str: Content of the file

    Raises:
        IsADirectoryError: If the path is a directory
        FileNotFoundError: If the file doesn't exist
        PermissionError: If there are permission issues
    """
    import os

    if os.path.isdir(file_path):
        raise IsADirectoryError(f"'{file_path}' is a directory, not a file")

    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task(args: argparse.Namespace, cli_multiline_input: bool) -> str:
    """
    Read the task from the CLI args, file, or stdin.
    """

    # Determine the task
    task_str = ''
    if args.file:
        try:
            task_str = read_task_from_file(args.file)
        except IsADirectoryError as e:
            print(f'Error: {e}')
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        except PermissionError:
            print(f"Error: Permission denied when reading '{args.file}'.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}")
            sys.exit(1)
    elif args.task:
        task_str = args.task
    elif not sys.stdin.isatty():
        task_str = read_input(cli_multiline_input)

    return task_str
