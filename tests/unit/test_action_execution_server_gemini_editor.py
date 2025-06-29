"""Unit tests for action execution server handling of Gemini file editor actions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.events.action import Action
from openhands.events.action.gemini_file_editor import (
    GeminiEditAction,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)
from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
)
from openhands.runtime.action_execution_server import ActionExecutor
from openhands.runtime.plugins.agent_skills.gemini_file_editor.gemini_file_editor import (
    GeminiFileEditor,
)


@pytest.fixture
def action_execution_server():
    """Create a mock action execution server for testing."""
    with patch(
        'openhands.runtime.action_execution_server.ActionExecutor.__init__',
        return_value=None,
    ):
        server = ActionExecutor(
            plugins_to_load=[],
            work_dir='/workspace',
            username='test',
            user_id=1000,
            browsergym_eval_env=None,
        )
        # Mock the lock
        server.lock = AsyncMock()
        server.lock.__aenter__.return_value = None
        server.lock.__aexit__.return_value = None

        # Mock the gemini_file_editor
        server.gemini_file_editor = MagicMock(spec=GeminiFileEditor)
        return server


@pytest.mark.asyncio
async def test_run_action_gemini_edit(action_execution_server):
    """Test that the action execution server correctly handles GeminiEditAction."""
    # Create a mock GeminiEditAction
    action = GeminiEditAction(
        file_path='/test/file.py',
        old_string="def hello():\n    print('Hello')",
        new_string="def hello():\n    print('Hello, World!')",
        expected_replacements=1,
    )

    # Mock the handle_edit_action method to return a FileEditObservation
    mock_observation = FileEditObservation(
        content="@@ -1,2 +1,2 @@\n def hello():\n-    print('Hello')\n+    print('Hello, World!')",
        path='/test/file.py',
        prev_exist=True,
        old_content="def hello():\n    print('Hello')",
        new_content="def hello():\n    print('Hello, World!')",
    )
    action_execution_server.gemini_file_editor.handle_edit_action.return_value = (
        mock_observation
    )

    # Call run_action
    observation = await action_execution_server.run_action(action)

    # Verify that the handle_edit_action method was called with the correct action
    action_execution_server.gemini_file_editor.handle_edit_action.assert_called_once_with(
        action
    )

    # Verify that the observation is correct
    assert observation == mock_observation
    assert isinstance(observation, FileEditObservation)
    assert observation.content == mock_observation.content
    assert observation.path == mock_observation.path
    assert observation.prev_exist == mock_observation.prev_exist
    assert observation.old_content == mock_observation.old_content
    assert observation.new_content == mock_observation.new_content


@pytest.mark.asyncio
async def test_run_action_gemini_write_file(action_execution_server):
    """Test that the action execution server correctly handles GeminiWriteFileAction."""
    # Create a mock GeminiWriteFileAction
    action = GeminiWriteFileAction(
        file_path='/test/file.py',
        content="def hello():\n    print('Hello, World!')",
    )

    # Mock the handle_write_file_action method to return a FileEditObservation
    mock_observation = FileEditObservation(
        content="@@ -0,0 +1,2 @@\n+def hello():\n+    print('Hello, World!')",
        path='/test/file.py',
        prev_exist=False,
        old_content='',
        new_content="def hello():\n    print('Hello, World!')",
    )
    action_execution_server.gemini_file_editor.handle_write_file_action.return_value = (
        mock_observation
    )

    # Call run_action
    observation = await action_execution_server.run_action(action)

    # Verify that the handle_write_file_action method was called with the correct action
    action_execution_server.gemini_file_editor.handle_write_file_action.assert_called_once_with(
        action
    )

    # Verify that the observation is correct
    assert observation == mock_observation
    assert isinstance(observation, FileEditObservation)
    assert observation.content == mock_observation.content
    assert observation.path == mock_observation.path
    assert observation.prev_exist == mock_observation.prev_exist
    assert observation.old_content == mock_observation.old_content
    assert observation.new_content == mock_observation.new_content


@pytest.mark.asyncio
async def test_run_action_gemini_read_file(action_execution_server):
    """Test that the action execution server correctly handles GeminiReadFileAction."""
    # Create a mock GeminiReadFileAction
    action = GeminiReadFileAction(
        absolute_path='/test/file.py',
    )

    # Mock the handle_read_file_action method to return a FileReadObservation
    mock_observation = FileReadObservation(
        content="def hello():\n    print('Hello, World!')",
        path='/test/file.py',
    )
    action_execution_server.gemini_file_editor.handle_read_file_action.return_value = (
        mock_observation
    )

    # Call run_action
    observation = await action_execution_server.run_action(action)

    # Verify that the handle_read_file_action method was called with the correct action
    action_execution_server.gemini_file_editor.handle_read_file_action.assert_called_once_with(
        action
    )

    # Verify that the observation is correct
    assert observation == mock_observation
    assert isinstance(observation, FileReadObservation)
    assert observation.content == mock_observation.content
    assert observation.path == mock_observation.path


@pytest.mark.asyncio
async def test_run_action_unsupported_action(action_execution_server):
    """Test that the action execution server correctly handles unsupported actions."""

    # Create a mock Action with an unsupported action type
    class UnsupportedAction(Action):
        action = 'unsupported_action'

    action = UnsupportedAction()

    # Call run_action
    observation = await action_execution_server.run_action(action)

    # Verify that an ErrorObservation is returned
    assert isinstance(observation, ErrorObservation)
    assert 'Action unsupported_action is not supported' in observation.content


@pytest.mark.asyncio
async def test_run_action_missing_method(action_execution_server):
    """Test that the action execution server correctly handles actions with missing methods."""

    # Create a mock Action with a valid action type but no corresponding method
    class MissingMethodAction(Action):
        action = 'missing_method'

    action = MissingMethodAction()

    # Call run_action
    observation = await action_execution_server.run_action(action)

    # Verify that an ErrorObservation is returned
    assert isinstance(observation, ErrorObservation)
    assert 'Action missing_method is not supported' in observation.content
