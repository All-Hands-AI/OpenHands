import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, Union

from openhands.events.observation import (
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)

T = TypeVar('T')

def file_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for file operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except PermissionError:
                return ErrorObservation(
                    f"You're not allowed to access this path. You can only access paths inside the workspace."
                )
            except FileNotFoundError:
                return ErrorObservation(f'File not found during {operation_name}')
            except UnicodeDecodeError:
                return ErrorObservation(f'File could not be decoded as utf-8 during {operation_name}')
            except IsADirectoryError:
                return ErrorObservation(f'Path is a directory. You can only {operation_name} files')
            except Exception as e:
                return ErrorObservation(f'Error during {operation_name}: {str(e)}')
        return wrapper
    return decorator


@file_operation("resolve_path")
def resolve_path(
    file_path: str,
    working_directory: str,
    workspace_base: str,
    workspace_mount_path_in_sandbox: str,
) -> Path:
    """Resolve a file path to a path on the host filesystem."""
    path_in_sandbox = Path(file_path)

    if not path_in_sandbox.is_absolute():
        path_in_sandbox = Path(working_directory) / path_in_sandbox

    abs_path_in_sandbox = path_in_sandbox.resolve()

    if not abs_path_in_sandbox.is_relative_to(workspace_mount_path_in_sandbox):
        raise PermissionError(f'File access not permitted: {file_path}')

    path_in_workspace = abs_path_in_sandbox.relative_to(
        Path(workspace_mount_path_in_sandbox)
    )

    path_in_host_workspace = Path(workspace_base) / path_in_workspace
    return path_in_host_workspace


def read_lines(all_lines: list[str], start: int = 0, end: int = -1) -> list[str]:
    """Read lines from a list with start and end indices."""
    start = max(0, min(start, len(all_lines)))
    end = -1 if end == -1 else max(end, 0)
    end = min(end, len(all_lines))
    
    if end == -1:
        return all_lines[start:]
    else:
        num_lines = len(all_lines)
        begin = max(0, min(start, num_lines - 2))
        end = -1 if end > num_lines else max(begin + 1, end)
        return all_lines[begin:end]


@file_operation("read")
async def read_file(
    path: str,
    workdir: str,
    workspace_base: str,
    workspace_mount_path_in_sandbox: str,
    start: int = 0,
    end: int = -1
) -> Observation:
    """Read file content with line range control."""
    whole_path = resolve_path(
        path, workdir, workspace_base, workspace_mount_path_in_sandbox
    )
    with open(whole_path, 'r', encoding='utf-8') as file:
        lines = read_lines(file.readlines(), start, end)
    return FileReadObservation(path=path, content=''.join(lines))


def insert_lines(
    to_insert: list[str],
    original: list[str],
    start: int = 0,
    end: int = -1
) -> list[str]:
    """Insert new content into original content based on start and end indices."""
    new_lines = [''] if start == 0 else original[:start]
    new_lines += [i + '\n' for i in to_insert]
    new_lines += [''] if end == -1 else original[end:]
    return new_lines


@file_operation("write")
async def write_file(
    path: str,
    workdir: str,
    workspace_base: str,
    workspace_mount_path_in_sandbox: str,
    content: str,
    start: int = 0,
    end: int = -1,
) -> Observation:
    """Write content to file with line range control."""
    insert = content.split('\n')
    whole_path = resolve_path(
        path, workdir, workspace_base, workspace_mount_path_in_sandbox
    )
    
    if not os.path.exists(os.path.dirname(whole_path)):
        os.makedirs(os.path.dirname(whole_path))
    
    mode = 'w' if not os.path.exists(whole_path) else 'r+'
    with open(whole_path, mode, encoding='utf-8') as file:
        if mode != 'w':
            all_lines = file.readlines()
            new_file = insert_lines(insert, all_lines, start, end)
        else:
            new_file = [i + '\n' for i in insert]

        file.seek(0)
        file.writelines(new_file)
        file.truncate()
    
    return FileWriteObservation(content='', path=path)

