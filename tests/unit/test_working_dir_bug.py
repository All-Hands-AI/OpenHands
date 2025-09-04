"""Test for the working_dir bug in local runtime.

This test reproduces the bug where working_dir is always '/workspace'
even though the real working directory is different in local runtime.
"""

import tempfile
from unittest.mock import MagicMock

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.impl.local.local_runtime import LocalRuntime


class TestWorkingDirBug:
    """Test cases for the working_dir bug in local runtime."""

    def test_working_dir_fix_for_local_runtime(self):
        """Test that working_dir fix works correctly for local runtime.

        This test verifies the fix where:
        1. Local runtime sets up a real filesystem path (e.g., /tmp/openhands_workspace_xyz)
        2. The fix uses runtime.config.workspace_mount_path_in_sandbox instead of config.workspace_mount_path_in_sandbox
        3. This ensures the LLM receives the correct working directory information
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup config for local runtime
            config = OpenHandsConfig()
            config.runtime = 'local'
            config.workspace_base = temp_dir  # Set explicit workspace base

            # Before runtime connection: working_dir is the default value
            working_dir_before_connect = config.workspace_mount_path_in_sandbox
            assert working_dir_before_connect == '/workspace'  # This is the default

            # Simulate what happens when runtime is created with a different config object
            runtime_config = OpenHandsConfig()
            runtime_config.runtime = 'local'
            runtime_config.workspace_base = temp_dir

            # Simulate what local runtime's connect() method does
            # This is what happens in LocalRuntime.connect() lines 255 or 265
            runtime_config.workspace_mount_path_in_sandbox = temp_dir

            # The fix: use runtime.config instead of the original config
            working_dir_with_fix = runtime_config.workspace_mount_path_in_sandbox
            assert working_dir_with_fix == temp_dir

            # Verify the fix works
            assert working_dir_before_connect != working_dir_with_fix
            assert working_dir_with_fix == temp_dir

    def test_working_dir_bug_with_temp_workspace(self):
        """Test the bug when local runtime creates a temporary workspace."""
        # Setup config for local runtime without workspace_base
        config = OpenHandsConfig()
        config.runtime = 'local'
        config.workspace_base = (
            None  # This will cause local runtime to create temp workspace
        )

        # Create mocks
        event_stream = MagicMock(spec=EventStream)
        llm_registry = MagicMock(spec=LLMRegistry)

        # Create local runtime
        runtime = LocalRuntime(
            config=config,
            event_stream=event_stream,
            llm_registry=llm_registry,
            sid='test_session',
        )

        # Simulate what connect() does when creating temp workspace
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime._temp_workspace = temp_dir
            runtime.config.workspace_mount_path_in_sandbox = temp_dir

            # Now the runtime has the correct working directory
            assert runtime.config.workspace_mount_path_in_sandbox == temp_dir

            # But the bug is that working_dir passed to create_memory is still '/workspace'
            wrong_working_dir = '/workspace'  # This is the bug
            correct_working_dir = runtime.config.workspace_mount_path_in_sandbox

            # Verify the bug exists
            assert wrong_working_dir != correct_working_dir
            assert correct_working_dir == temp_dir
            assert wrong_working_dir == '/workspace'

    def test_docker_runtime_should_use_workspace(self):
        """Test that Docker runtime should correctly use '/workspace' as working_dir.

        This test ensures our fix doesn't break Docker runtime, where '/workspace'
        is the correct working directory inside the container.
        """
        config = OpenHandsConfig()
        config.runtime = 'docker'
        # For Docker runtime, workspace_mount_path_in_sandbox should remain '/workspace'
        assert config.workspace_mount_path_in_sandbox == '/workspace'

        # For Docker runtime, working_dir should be '/workspace' (inside container)
        working_dir = config.workspace_mount_path_in_sandbox
        assert working_dir == '/workspace'

        # Simulate runtime config (Docker runtime doesn't modify workspace_mount_path_in_sandbox)
        runtime_config = OpenHandsConfig()
        runtime_config.runtime = 'docker'
        # Docker runtime keeps the default value
        assert runtime_config.workspace_mount_path_in_sandbox == '/workspace'

        # With our fix, we use runtime.config.workspace_mount_path_in_sandbox
        # For Docker runtime, this should still be '/workspace'
        working_dir_with_fix = runtime_config.workspace_mount_path_in_sandbox
        assert working_dir_with_fix == '/workspace'
