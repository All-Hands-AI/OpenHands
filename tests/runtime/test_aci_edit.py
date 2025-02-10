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
