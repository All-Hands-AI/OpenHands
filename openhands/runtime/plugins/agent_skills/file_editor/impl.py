from collections import defaultdict
from pathlib import Path
from typing import Literal, get_args

from .base import CLIResult, ToolError, ToolResult
from .run import maybe_truncate, run

Command = Literal[
    'view',
    'create',
    'str_replace',
    'insert',
    'undo_edit',
]
SNIPPET_LINES: int = 4


class EditTool:
    """
    An filesystem editor tool that allows the agent to view, create, and edit files.
    The tool parameters are defined by Anthropic and are not editable.

    Original implementation: https://github.com/anthropics/anthropic-quickstarts/blob/main/computer-use-demo/computer_use_demo/tools/edit.py
    """

    _file_history: dict[Path, list[str]]

    def __init__(self):
        self._file_history = defaultdict(list)
        super().__init__()

    def __call__(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs,
    ):
        _path = Path(path)
        self.validate_path(command, _path)
        if command == 'view':
            return self.view(_path, view_range)
        elif command == 'create':
            if file_text is None:
                raise ToolError('Parameter `file_text` is required for command: create')
            self.write_file(_path, file_text)
            self._file_history[_path].append(file_text)
            return ToolResult(output=f'File created successfully at: {_path}')
        elif command == 'str_replace':
            if old_str is None:
                raise ToolError(
                    'Parameter `old_str` is required for command: str_replace'
                )
            return self.str_replace(_path, old_str, new_str)
        elif command == 'insert':
            if insert_line is None:
                raise ToolError(
                    'Parameter `insert_line` is required for command: insert'
                )
            if new_str is None:
                raise ToolError('Parameter `new_str` is required for command: insert')
            return self.insert(_path, insert_line, new_str)
        elif command == 'undo_edit':
            return self.undo_edit(_path)
        raise ToolError(
            f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}'
        )

    def validate_path(self, command: str, path: Path):
        """
        Check that the path/command combination is valid.
        """
        # Check if its an absolute path
        if not path.is_absolute():
            suggested_path = Path('') / path
            raise ToolError(
                f'The path {path} is not an absolute path, it should start with `/`. Maybe you meant {suggested_path}?'
            )
        # Check if path exists
        if not path.exists() and command != 'create':
            raise ToolError(
                f'The path {path} does not exist. Please provide a valid path.'
            )
        if path.exists() and command == 'create':
            raise ToolError(
                f'File already exists at: {path}. Cannot overwrite files using command `create`.'
            )
        # Check if the path points to a directory
        if path.is_dir():
            if command != 'view':
                raise ToolError(
                    f'The path {path} is a directory and only the `view` command can be used on directories'
                )

    def view(self, path: Path, view_range: list[int] | None = None):
        """Implement the view command"""
        if path.is_dir():
            if view_range:
                raise ToolError(
                    'The `view_range` parameter is not allowed when `path` points to a directory.'
                )

            _, stdout, stderr = run(rf"find {path} -maxdepth 2 -not -path '*/\.*'")
            if not stderr:
                stdout = f"Here's the files and directories up to 2 levels deep in {path}, excluding hidden items:\n{stdout}\n"
            return CLIResult(output=stdout, error=stderr)

        file_content = self.read_file(path)
        init_line = 1
        if view_range:
            if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                raise ToolError(
                    'Invalid `view_range`. It should be a list of two integers.'
                )
            file_lines = file_content.split('\n')
            n_lines_file = len(file_lines)
            init_line, final_line = view_range
            if init_line < 1 or init_line > n_lines_file:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. It's first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
                )
            if final_line > n_lines_file:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. It's second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
                )
            if final_line != -1 and final_line < init_line:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. It's second element `{final_line}` should be larger or equal than its first `{init_line}`"
                )

            if final_line == -1:
                file_content = '\n'.join(file_lines[init_line - 1 :])
            else:
                file_content = '\n'.join(file_lines[init_line - 1 : final_line])

        return CLIResult(
            output=self._make_output(file_content, str(path), init_line=init_line)
        )

    def str_replace(self, path: Path, old_str: str, new_str: str | None):
        """Implement the str_replace command, which replaces old_str with new_str in the file content"""
        # Read the file content
        file_content = self.read_file(path).expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str is not None else ''

        # Check if old_str is unique in the file
        occurrences = file_content.count(old_str)
        if occurrences == 0:
            raise ToolError(
                f'No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.'
            )
        elif occurrences > 1:
            file_content_lines = file_content.split('\n')
            lines = [
                idx + 1
                for idx, line in enumerate(file_content_lines)
                if old_str in line
            ]
            raise ToolError(
                f'No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique'
            )

        # Replace old_str with new_str
        new_file_content = file_content.replace(old_str, new_str)

        # Write the new content to the file
        self.write_file(path, new_file_content)

        # Save the content to history
        self._file_history[path].append(file_content)

        # Create a snippet of the edited section
        replacement_line = file_content.split(old_str)[0].count('\n')
        start_line = max(0, replacement_line - SNIPPET_LINES)
        end_line = replacement_line + SNIPPET_LINES + new_str.count('\n')
        snippet = '\n'.join(new_file_content.split('\n')[start_line : end_line + 1])

        # Prepare the success message
        success_msg = f'The file {path} has been edited. '
        success_msg += self._make_output(
            snippet, f'a snippet of {path}', start_line + 1
        )
        success_msg += 'Review the changes and make sure they are as expected. Edit the file again if necessary.'

        return CLIResult(output=success_msg)

    def insert(self, path: Path, insert_line: int, new_str: str):
        """Implement the insert command, which inserts new_str at the specified line in the file content."""
        file_text = self.read_file(path).expandtabs()
        new_str = new_str.expandtabs()
        file_text_lines = file_text.split('\n')
        n_lines_file = len(file_text_lines)

        if insert_line < 0 or insert_line > n_lines_file:
            raise ToolError(
                f'Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: {[0, n_lines_file]}'
            )

        new_str_lines = new_str.split('\n')
        new_file_text_lines = (
            file_text_lines[:insert_line]
            + new_str_lines
            + file_text_lines[insert_line:]
        )
        snippet_lines = (
            file_text_lines[max(0, insert_line - SNIPPET_LINES) : insert_line]
            + new_str_lines
            + file_text_lines[insert_line : insert_line + SNIPPET_LINES]
        )

        new_file_text = '\n'.join(new_file_text_lines)
        snippet = '\n'.join(snippet_lines)

        self.write_file(path, new_file_text)
        self._file_history[path].append(file_text)

        success_msg = f'The file {path} has been edited. '
        success_msg += self._make_output(
            snippet,
            'a snippet of the edited file',
            max(1, insert_line - SNIPPET_LINES + 1),
        )
        success_msg += 'Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary.'
        return CLIResult(output=success_msg)

    def undo_edit(self, path: Path):
        """Implement the undo_edit command."""
        if not self._file_history[path]:
            raise ToolError(f'No edit history found for {path}.')

        old_text = self._file_history[path].pop()
        self.write_file(path, old_text)

        return CLIResult(
            output=f'Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}'
        )

    def read_file(self, path: Path):
        """Read the content of a file from a given path; raise a ToolError if an error occurs."""
        try:
            return path.read_text()
        except Exception as e:
            raise ToolError(f'Ran into {e} while trying to read {path}') from None

    def write_file(self, path: Path, file: str):
        """Write the content of a file to a given path; raise a ToolError if an error occurs."""
        try:
            path.write_text(file)
        except Exception as e:
            raise ToolError(f'Ran into {e} while trying to write to {path}') from None

    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ):
        """Generate output for the CLI based on the content of a file."""
        file_content = maybe_truncate(file_content)
        if expand_tabs:
            file_content = file_content.expandtabs()
        file_content = '\n'.join(
            [
                f'{i + init_line:6}\t{line}'
                for i, line in enumerate(file_content.split('\n'))
            ]
        )
        return (
            f"Here's the result of running `cat -n` on {file_descriptor}:\n"
            + file_content
            + '\n'
        )
