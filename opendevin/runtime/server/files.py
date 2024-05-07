import os
from pathlib import Path

from opendevin.core import config
from opendevin.core.schema.config import ConfigType
from opendevin.events.observation import (
    AgentErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)


def resolve_path(file_path, working_directory):
    path_in_sandbox = Path(file_path)

    # Apply working directory
    if not path_in_sandbox.is_absolute():
        path_in_sandbox = Path(working_directory) / path_in_sandbox

    # Sanitize the path with respect to the root of the full sandbox
    # (deny any .. path traversal to parent directories of the sandbox)
    abs_path_in_sandbox = path_in_sandbox.resolve()

    # If the path is outside the workspace, deny it
    if not abs_path_in_sandbox.is_relative_to(
        config.get(ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX)
    ):
        raise PermissionError(f'File access not permitted: {file_path}')

    # Get path relative to the root of the workspace inside the sandbox
    path_in_workspace = abs_path_in_sandbox.relative_to(
        Path(config.get(ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX))
    )

    # Get path relative to host
    path_in_host_workspace = (
        Path(config.get(ConfigType.WORKSPACE_BASE)) / path_in_workspace
    )

    return path_in_host_workspace


def _read_lines(action, all_lines: list[str]):
    if action.end == -1:
        if action.start == 0:
            return all_lines
        else:
            return all_lines[action.start :]
    else:
        num_lines = len(all_lines)
        begin = max(0, min(action.start, num_lines - 2))
        end = -1 if action.end > num_lines else max(begin + 1, action.end)
        return all_lines[begin:end]


async def read_file(action, workdir) -> Observation:
    try:
        whole_path = resolve_path(action.path, workdir)
        action.start = max(action.start, 0)
        try:
            with open(whole_path, 'r', encoding='utf-8') as file:
                read_lines = action._read_lines(file.readlines())
                code_view = ''.join(read_lines)
        except FileNotFoundError:
            return AgentErrorObservation(f'File not found: {action.path}')
        except UnicodeDecodeError:
            return AgentErrorObservation(
                f'File could not be decoded as utf-8: {action.path}'
            )
        except IsADirectoryError:
            return AgentErrorObservation(
                f'Path is a directory: {action.path}. You can only read files'
            )
    except PermissionError:
        return AgentErrorObservation(f'Malformed paths not permitted: {action.path}')
    return FileReadObservation(path=action.path, content=code_view)


def _insert_lines(action, to_insert: list[str], original: list[str]):
    """
    Insert the new content to the original content based on action.start and action.end
    """
    new_lines = [''] if action.start == 0 else original[: action.start]
    new_lines += [i + '\n' for i in to_insert]
    new_lines += [''] if action.end == -1 else original[action.end :]
    return new_lines


async def write_file(action, workdir) -> Observation:
    insert = action.content.split('\n')

    try:
        whole_path = resolve_path(action.path, workdir)
        if not os.path.exists(os.path.dirname(whole_path)):
            os.makedirs(os.path.dirname(whole_path))
        mode = 'w' if not os.path.exists(whole_path) else 'r+'
        try:
            with open(whole_path, mode, encoding='utf-8') as file:
                if mode != 'w':
                    all_lines = file.readlines()
                    new_file = action._insert_lines(insert, all_lines)
                else:
                    new_file = [i + '\n' for i in insert]

                file.seek(0)
                file.writelines(new_file)
                file.truncate()
        except FileNotFoundError:
            return AgentErrorObservation(f'File not found: {action.path}')
        except IsADirectoryError:
            return AgentErrorObservation(
                f'Path is a directory: {action.path}. You can only write to files'
            )
        except UnicodeDecodeError:
            return AgentErrorObservation(
                f'File could not be decoded as utf-8: {action.path}'
            )
    except PermissionError:
        return AgentErrorObservation(f'Malformed paths not permitted: {action.path}')
    return FileWriteObservation(content='', path=action.path)
