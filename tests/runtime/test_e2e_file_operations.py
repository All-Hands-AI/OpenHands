import os

from conftest import (
    _close_test_runtime,
    _load_runtime,
)

from openhands.controller.state.state import State
from openhands.events.action import (
    FileReadAction,
    FileWriteAction,
)
from openhands.events.observation import (
    FileReadObservation,
    FileWriteObservation,
)


def test_e2e_file_write_read_edit_operations(temp_dir, runtime_cls, run_as_openhands):
    """
    Test a sequence of file operations: write, read, and edit.
    """
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    try:
        State(
            inputs={'task': 'E2E file operations test'},
            history=[],
        )

        filename = 'test_script.py'
        expected_full_path = os.path.join(
            config.workspace_mount_path_in_sandbox, filename
        )

        original_content = "print('Hello, World!')"
        added_content = "\nprint('This is a new line.')"
        # It's good practice for text files to end with a newline.
        # Let's ensure our expected content reflects this if the system adds it.
        # Or, we can strip during comparison. Let's try stripping first.
        final_content = original_content + added_content

        # 1. Write a new file
        write_action = FileWriteAction(path=filename, content=original_content)
        print(f'Executing action: {write_action}')
        obs = runtime.run_action(write_action)
        print(f'Observation from write: {obs}')
        assert isinstance(obs, FileWriteObservation), (
            f'Expected FileWriteObservation, got {type(obs)}'
        )
        assert obs.path == expected_full_path, (
            f'FileWriteObservation path mismatch. Expected {expected_full_path}, got {obs.path}'
        )

        # 2. Read the file
        read_action = FileReadAction(path=filename)
        print(f'Executing action: {read_action}')
        obs = runtime.run_action(read_action)
        print(f'Observation from read: {obs}')
        assert isinstance(obs, FileReadObservation), (
            f'Expected FileReadObservation, got {type(obs)}'
        )
        assert obs.path == expected_full_path, (
            f'FileReadObservation path mismatch. Expected {expected_full_path}, got {obs.path}'
        )
        assert obs.content.strip() == original_content.strip(), (
            'FileReadObservation content mismatch after initial write'
        )

        # 3. Edit the file (overwrite with new combined content)
        edit_action = FileWriteAction(path=filename, content=final_content)
        print(f'Executing action: {edit_action}')
        obs = runtime.run_action(edit_action)
        print(f'Observation from edit: {obs}')
        assert isinstance(obs, FileWriteObservation), (
            f'Expected FileWriteObservation for edit, got {type(obs)}'
        )
        assert obs.path == expected_full_path, (
            f'FileWriteObservation path mismatch on edit. Expected {expected_full_path}, got {obs.path}'
        )

        # 4. Read the modified file to confirm edit
        read_action_after_edit = FileReadAction(path=filename)
        print(f'Executing action: {read_action_after_edit}')
        obs = runtime.run_action(read_action_after_edit)
        print(f'Observation from read after edit: {obs}')
        assert isinstance(obs, FileReadObservation), (
            f'Expected FileReadObservation after edit, got {type(obs)}'
        )
        assert obs.path == expected_full_path, (
            f'FileReadObservation path mismatch after edit. Expected {expected_full_path}, got {obs.path}'
        )
        assert obs.content.strip() == final_content.strip(), (
            'FileReadObservation content mismatch after edit'
        )

        print('E2E file operations test completed successfully.')
    finally:
        _close_test_runtime(runtime)


# To run this test:
# poetry run pytest tests/runtime/test_e2e_file_operations.py -v
# or specifically for LocalRuntime:
# TEST_RUNTIME=local poetry run pytest tests/runtime/test_e2e_file_operations.py -v
