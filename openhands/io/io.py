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
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task(args: argparse.Namespace, cli_multiline_input: bool) -> str:
    """
    Read the task from the CLI args, file, or stdin.
    """

    # Determine the task
    task_str = ''
    if args.file:
        file_content = read_task_from_file(args.file)
        # For CLI usage, enhance the file content with a prompt
        # that instructs the agent to read and understand the file first
        task_str = f"""The user has tagged a file '{args.file}'.
Please read and understand the following file content first:

```
{file_content}
```

After reviewing the file, please ask the user what they would like to do with it."""
    elif args.task:
        task_str = args.task
    elif not sys.stdin.isatty():
        task_str = read_input(cli_multiline_input)

    return task_str
