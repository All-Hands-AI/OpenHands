"""Unit tests for task tracker storage functionality."""

import tempfile
from unittest.mock import MagicMock

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.events.action import TaskTrackingAction
from openhands.events.observation import TaskTrackingObservation
from openhands.runtime.impl.local.local_runtime import LocalRuntime
from openhands.storage.local import LocalFileStore


@pytest.fixture
def config():
    """Create a mock OpenHandsConfig for testing."""
    config = OpenHandsConfig()
    config.sandbox.local_runtime_url = 'http://localhost'
    config.workspace_mount_path_in_sandbox = '/workspace'
    return config


@pytest.fixture
def temp_file_store():
    """Create a temporary file store for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield LocalFileStore(temp_dir)


@pytest.fixture
def event_stream(temp_file_store):
    """Create a mock EventStream with a real file store for testing."""
    stream = MagicMock(spec=EventStream)
    stream.file_store = temp_file_store
    stream.user_id = None  # CLI mode
    return stream


@pytest.fixture
def local_runtime(config, event_stream):
    """Create a LocalRuntime instance for testing."""
    # Use __new__ to avoid calling __init__ which would start the server
    runtime = LocalRuntime.__new__(LocalRuntime)
    runtime.config = config
    runtime.event_stream = event_stream
    runtime.sid = 'test-session-123'
    runtime._runtime_initialized = True

    # Mock the runtime_url property for testing
    def mock_runtime_url(self):
        return 'http://localhost'

    # Create a property mock for runtime_url
    type(runtime).runtime_url = property(mock_runtime_url)

    return runtime


def test_task_tracker_plan_command(local_runtime):
    """Test that the plan command stores tasks in the session directory."""
    # Create a task tracking action with a plan command
    task_list = [
        {
            'id': 'task-1',
            'title': 'Test task 1',
            'status': 'todo',
            'notes': 'This is a test task',
        },
        {
            'id': 'task-2',
            'title': 'Test task 2',
            'status': 'in_progress',
            'notes': 'Another test task',
        },
    ]

    action = TaskTrackingAction(command='plan', task_list=task_list)

    # Run the action
    observation = local_runtime.run_action(action)

    # Verify the observation is successful
    assert isinstance(observation, TaskTrackingObservation)
    assert observation.command == 'plan'
    assert len(observation.task_list) == 2
    assert 'Task list has been updated with 2 items' in observation.content
    assert 'sessions/test-session-123/TASKS.md' in observation.content

    # Verify the file was written to the correct location
    expected_path = 'sessions/test-session-123/TASKS.md'
    content = local_runtime.event_stream.file_store.read(expected_path)

    # Verify the content format
    assert '# Task List' in content
    assert '⏳ Test task 1' in content
    assert '🔄 Test task 2' in content
    assert 'This is a test task' in content
    assert 'Another test task' in content


def test_task_tracker_view_command_with_existing_file(local_runtime):
    """Test that the view command reads tasks from the session directory."""
    # First create a task file
    task_list = [
        {
            'id': 'task-1',
            'title': 'Existing task',
            'status': 'done',
            'notes': 'Completed task',
        }
    ]

    plan_action = TaskTrackingAction(command='plan', task_list=task_list)
    local_runtime.run_action(plan_action)

    # Now test the view command
    view_action = TaskTrackingAction(command='view')
    observation = local_runtime.run_action(view_action)

    # Verify the observation
    assert isinstance(observation, TaskTrackingObservation)
    assert observation.command == 'view'
    assert '# Task List' in observation.content
    assert '✅ Existing task' in observation.content
    assert 'Completed task' in observation.content


def test_task_tracker_view_command_no_file(local_runtime):
    """Test that the view command handles missing task files gracefully."""
    view_action = TaskTrackingAction(command='view')
    observation = local_runtime.run_action(view_action)

    # Verify the observation handles missing file
    assert isinstance(observation, TaskTrackingObservation)
    assert observation.command == 'view'
    assert 'No task list found' in observation.content
    assert 'Use the "plan" command to create one' in observation.content


def test_task_tracker_file_path_generation(local_runtime):
    """Test that the task file path is generated correctly."""
    expected_path = 'sessions/test-session-123/TASKS.md'
    actual_path = local_runtime._get_task_file_path()
    assert actual_path == expected_path


def test_task_tracker_with_user_id(local_runtime):
    """Test task tracker with user ID (server mode)."""
    # Set user ID to simulate server mode
    local_runtime.event_stream.user_id = 'user-456'

    expected_path = 'users/user-456/conversations/test-session-123/TASKS.md'
    actual_path = local_runtime._get_task_file_path()
    assert actual_path == expected_path

    # Test that plan command works with user ID
    task_list = [
        {
            'id': 'task-1',
            'title': 'Server mode task',
            'status': 'todo',
            'notes': 'Task in server mode',
        }
    ]

    action = TaskTrackingAction(command='plan', task_list=task_list)

    observation = local_runtime.run_action(action)
    assert isinstance(observation, TaskTrackingObservation)
    assert (
        'users/user-456/conversations/test-session-123/TASKS.md' in observation.content
    )
