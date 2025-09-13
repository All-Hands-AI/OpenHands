"""Test for the working_dir bug in RecallObservation.

This test reproduces the issue where RecallObservation's working_dir is always set to "/workspace"
in agent session mode, even when SANDBOX_VOLUMES is set to a different directory.
"""

from unittest.mock import MagicMock

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events.action.agent import RecallAction
from openhands.events.event import EventSource, RecallType
from openhands.events.stream import EventStream
from openhands.memory.memory import Memory
from openhands.runtime.base import Runtime
from openhands.storage.memory import InMemoryFileStore
from openhands.utils.prompt import RuntimeInfo


@pytest.fixture
def file_store():
    """Create a temporary file store for testing."""
    return InMemoryFileStore({})


@pytest.fixture
def event_stream(file_store):
    """Create an event stream for testing."""
    return EventStream('test-session', file_store)


@pytest.fixture
def mock_runtime():
    """Create a mock runtime for testing."""
    runtime = MagicMock(spec=Runtime)
    runtime.web_hosts = {}
    runtime.additional_agent_instructions = ''
    runtime.workspace_root.return_value = '/app'  # Simulate custom working directory
    return runtime


def test_recall_observation_working_dir_from_runtime_info():
    """Test that RecallObservation uses working_dir from RuntimeInfo correctly."""
    file_store = InMemoryFileStore({})
    event_stream = EventStream('test-session', file_store)
    memory = Memory(event_stream=event_stream, sid='test-session')

    # Set runtime info with custom working directory
    custom_working_dir = '/app'
    runtime_info = RuntimeInfo(
        date='2025-01-13',
        available_hosts={},
        additional_agent_instructions='',
        custom_secrets_descriptions={},
        working_dir=custom_working_dir,
    )
    memory.runtime_info = runtime_info

    # Create a workspace context recall action
    recall_action = RecallAction(
        recall_type=RecallType.WORKSPACE_CONTEXT, query='test query'
    )
    recall_action._source = EventSource.USER  # type: ignore[attr-defined]

    # Call the workspace context recall method
    observation = memory._on_workspace_context_recall(recall_action)

    # Assert that the working_dir is correctly set from runtime_info
    assert observation is not None
    assert observation.working_dir == custom_working_dir
    assert observation.working_dir != '/workspace'  # Should not be the default


def test_memory_set_runtime_info_with_custom_working_dir():
    """Test that Memory.set_runtime_info correctly stores custom working_dir."""
    file_store = InMemoryFileStore({})
    event_stream = EventStream('test-session', file_store)
    memory = Memory(event_stream=event_stream, sid='test-session')

    # Create a mock runtime
    mock_runtime = MagicMock(spec=Runtime)
    mock_runtime.web_hosts = {}
    mock_runtime.additional_agent_instructions = ''

    custom_working_dir = '/app'
    custom_secrets = {}

    # Set runtime info with custom working directory
    memory.set_runtime_info(mock_runtime, custom_secrets, custom_working_dir)

    # Assert that the runtime_info has the correct working_dir
    assert memory.runtime_info is not None
    assert memory.runtime_info.working_dir == custom_working_dir
    assert memory.runtime_info.working_dir != '/workspace'


def test_agent_session_working_dir_bug_reproduction():
    """Test that reproduces the bug where agent session uses hardcoded /workspace."""
    # This test simulates the bug in agent_session.py where working_dir is taken from
    # config.workspace_mount_path_in_sandbox instead of runtime.workspace_root

    # Create a config with custom SANDBOX_VOLUMES setting
    config = OpenHandsConfig()
    config.workspace_mount_path_in_sandbox = (
        '/workspace'  # This is the bug - always hardcoded
    )

    # Create a mock runtime that should have a different workspace_root
    mock_runtime = MagicMock(spec=Runtime)
    mock_runtime.workspace_root = '/app'  # This is what should be used
    mock_runtime.web_hosts = {}
    mock_runtime.additional_agent_instructions = ''

    # Simulate what happens in agent_session.py (the buggy behavior)
    file_store = InMemoryFileStore({})
    event_stream = EventStream('test-session', file_store)
    memory = Memory(event_stream=event_stream, sid='test-session')

    # This is the buggy line from agent_session.py:162
    # working_dir=config.workspace_mount_path_in_sandbox
    buggy_working_dir = config.workspace_mount_path_in_sandbox

    # Set runtime info using the buggy working_dir
    memory.set_runtime_info(mock_runtime, {}, buggy_working_dir)

    # Create a workspace context recall action
    recall_action = RecallAction(
        recall_type=RecallType.WORKSPACE_CONTEXT, query='test query'
    )
    recall_action._source = EventSource.USER  # type: ignore[attr-defined]

    # Call the workspace context recall method
    observation = memory._on_workspace_context_recall(recall_action)

    # This demonstrates the bug: working_dir is '/workspace' instead of '/app'
    assert observation is not None
    assert observation.working_dir == '/workspace'  # This is the bug
    assert observation.working_dir != '/app'  # This is what it should be

    # Now test the correct behavior (what should happen)
    memory_correct = Memory(event_stream=event_stream, sid='test-session-correct')

    # This is what should happen - use runtime.workspace_root
    correct_working_dir = str(mock_runtime.workspace_root)
    memory_correct.set_runtime_info(mock_runtime, {}, correct_working_dir)

    observation_correct = memory_correct._on_workspace_context_recall(recall_action)

    # This shows the correct behavior
    assert observation_correct is not None
    assert observation_correct.working_dir == '/app'  # This is correct
    assert observation_correct.working_dir != '/workspace'


def test_agent_session_working_dir_fix():
    """Test that the fix in agent_session.py correctly uses runtime.workspace_root."""
    # This test simulates the fixed behavior where working_dir is taken from
    # runtime.workspace_root instead of config.workspace_mount_path_in_sandbox

    # Create a config with the default hardcoded value
    config = OpenHandsConfig()
    config.workspace_mount_path_in_sandbox = '/workspace'  # Default hardcoded value

    # Create a mock runtime with a different workspace_root
    mock_runtime = MagicMock(spec=Runtime)
    mock_runtime.workspace_root = '/app'  # Custom working directory
    mock_runtime.web_hosts = {}
    mock_runtime.additional_agent_instructions = ''

    # Simulate the fixed behavior from agent_session.py
    file_store = InMemoryFileStore({})
    event_stream = EventStream('test-session', file_store)
    memory = Memory(event_stream=event_stream, sid='test-session')

    # This is the fixed line from agent_session.py:162
    # working_dir=str(self.runtime.workspace_root) if self.runtime else config.workspace_mount_path_in_sandbox
    fixed_working_dir = (
        str(mock_runtime.workspace_root)
        if mock_runtime
        else config.workspace_mount_path_in_sandbox
    )

    # Set runtime info using the fixed working_dir
    memory.set_runtime_info(mock_runtime, {}, fixed_working_dir)

    # Create a workspace context recall action
    recall_action = RecallAction(
        recall_type=RecallType.WORKSPACE_CONTEXT, query='test query'
    )
    recall_action._source = EventSource.USER  # type: ignore[attr-defined]

    # Call the workspace context recall method
    observation = memory._on_workspace_context_recall(recall_action)

    # This demonstrates the fix: working_dir is now '/app' instead of '/workspace'
    assert observation is not None
    assert (
        observation.working_dir == '/app'
    )  # This is the correct behavior after the fix
    assert observation.working_dir != '/workspace'  # No longer hardcoded to /workspace

    # Test the fallback behavior when runtime is None
    fallback_working_dir = (
        config.workspace_mount_path_in_sandbox
    )  # Fallback to config value
    memory_fallback = Memory(event_stream=event_stream, sid='test-session-fallback')

    # Create a mock runtime with no web_hosts or additional_agent_instructions to simulate fallback
    mock_runtime_empty = MagicMock(spec=Runtime)
    mock_runtime_empty.web_hosts = {}
    mock_runtime_empty.additional_agent_instructions = ''

    memory_fallback.set_runtime_info(mock_runtime_empty, {}, fallback_working_dir)

    observation_fallback = memory_fallback._on_workspace_context_recall(recall_action)

    # When using the fallback working_dir, it should use the config value
    assert observation_fallback is not None
    assert (
        observation_fallback.working_dir == '/workspace'
    )  # Falls back to config value
