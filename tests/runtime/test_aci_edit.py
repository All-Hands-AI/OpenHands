"""Editor-related tests for the DockerRuntime."""

import os

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import FileEditAction, FileWriteAction


def test_view_file(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.\nThis file is for testing purposes.',
            path=test_file,
        )
        obs = runtime.run_action(action)

        # Test view command
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)

        assert f"Here's the result of running `cat -n` on {test_file}:" in obs.content
        assert '1\tThis is a test file.' in obs.content
        assert '2\tThis file is for testing purposes.' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_view_directory(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.\nThis file is for testing purposes.',
            path=test_file,
        )
        obs = runtime.run_action(action)

        # Test view command
        action = FileEditAction(
            command='view',
            path=config.workspace_mount_path_in_sandbox,
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert (
            obs.content
            == f"""Here's the files and directories up to 2 levels deep in {config.workspace_mount_path_in_sandbox}, excluding hidden items:
{config.workspace_mount_path_in_sandbox}/
{config.workspace_mount_path_in_sandbox}/test.txt"""
        )

    finally:
        _close_test_runtime(runtime)

# New tests start here

def test_create_file(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        new_file = os.path.join(config.workspace_mount_path_in_sandbox, 'new_file.txt')
        action = FileEditAction(
            command='create',
            path=new_file,
            file_text='New file content',
        )
        obs = runtime.run_action(action)
        assert 'File created successfully' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=new_file,
        )
        obs = runtime.run_action(action)
        assert 'New file content' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_str_replace(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.\nThis file is for testing purposes.',
            path=test_file,
        )
        runtime.run_action(action)

        # Test str_replace command
        action = FileEditAction(
            command='str_replace',
            path=test_file,
            old_str='test file',
            new_str='sample file',
        )
        obs = runtime.run_action(action)
        assert 'The file has been edited' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'This is a sample file.' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_insert(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='Line 1\nLine 2',
            path=test_file,
        )
        runtime.run_action(action)

        # Test insert command
        action = FileEditAction(
            command='insert',
            path=test_file,
            insert_line=1,
            new_str='Inserted line',
        )
        obs = runtime.run_action(action)
        assert 'The file has been edited' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'Line 1\nInserted line\nLine 2' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_undo_edit(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.',
            path=test_file,
        )
        runtime.run_action(action)

        # Make an edit
        action = FileEditAction(
            command='str_replace',
            path=test_file,
            old_str='test',
            new_str='sample',
        )
        runtime.run_action(action)

        # Undo the edit
        action = FileEditAction(
            command='undo_edit',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'Last edit to' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'This is a test file.' in obs.content

    finally:
        _close_test_runtime(runtime)
