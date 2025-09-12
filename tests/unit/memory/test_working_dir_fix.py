"""
Test for working_dir bug fix in workspace context recall.

This test verifies that the working_dir in workspace context recall
correctly reflects the runtime's actual workspace root instead of
the hardcoded config value.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events.action.agent import RecallAction
from openhands.events.observation.agent import RecallType
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def file_store():
    """Create a temporary file store for testing."""
    return InMemoryFileStore({})


@pytest.fixture
def mock_runtime():
    """Create a mock runtime for testing."""
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {}
    runtime.additional_agent_instructions = ''
    runtime.config = OpenHandsConfig()
    return runtime


def test_working_dir_uses_runtime_workspace_root(file_store, mock_runtime):
    """Test that working_dir correctly uses runtime.workspace_root."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up mock runtime with actual working directory
        actual_working_dir = temp_dir
        mock_runtime.workspace_root = Path(actual_working_dir)

        # Create event stream and memory
        event_stream = EventStream('test_sid', file_store)
        memory = Memory(event_stream, 'test_sid')

        # Set runtime info using the runtime workspace_root (the fix)
        memory.set_runtime_info(mock_runtime, {}, str(mock_runtime.workspace_root))

        # Trigger workspace context recall
        recall_action = RecallAction(
            recall_type=RecallType.WORKSPACE_CONTEXT, query='test query'
        )

        # Get the workspace context observation
        workspace_obs = memory._on_workspace_context_recall(recall_action)

        # Verify that working_dir matches the runtime's workspace_root
        assert workspace_obs.working_dir == str(actual_working_dir)
        assert workspace_obs.working_dir == str(mock_runtime.workspace_root)


def test_working_dir_bug_reproduction(file_store, mock_runtime):
    """Test that demonstrates the original bug with hardcoded config value."""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up mock runtime with actual working directory
        actual_working_dir = temp_dir
        mock_runtime.workspace_root = Path(actual_working_dir)

        # Create event stream and memory
        event_stream = EventStream('test_sid', file_store)
        memory = Memory(event_stream, 'test_sid')

        # Set runtime info using the hardcoded config value (the bug)
        config = mock_runtime.config
        memory.set_runtime_info(
            mock_runtime, {}, config.workspace_mount_path_in_sandbox
        )

        # Trigger workspace context recall
        recall_action = RecallAction(
            recall_type=RecallType.WORKSPACE_CONTEXT, query='test query'
        )

        # Get the workspace context observation
        workspace_obs = memory._on_workspace_context_recall(recall_action)

        # Verify that working_dir incorrectly uses the config value instead of actual directory
        assert workspace_obs.working_dir == config.workspace_mount_path_in_sandbox
        assert workspace_obs.working_dir != str(actual_working_dir)
        assert workspace_obs.working_dir != str(mock_runtime.workspace_root)
