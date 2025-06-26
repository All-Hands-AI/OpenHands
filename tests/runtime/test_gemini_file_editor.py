"""Tests for Gemini-style file editing tools."""

import os

import pytest
from conftest import _close_test_runtime, _load_runtime

from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
)
from openhands.runtime.plugins.agent_skills.gemini_file_editor.gemini_file_editor import (
    GeminiEditAction,
    GeminiFileEditor,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)


def test_gemini_edit_action():
    """Test GeminiEditAction."""
    action = GeminiEditAction(
        file_path='/test/file.py',
        old_string="def hello():\n    print('Hello')",
        new_string="def hello():\n    print('Hello, World!')",
        expected_replacements=1,
    )

    # Test to_dict method
    action_dict = action.to_dict()
    assert action_dict['file_path'] == '/test/file.py'
    assert action_dict['old_string'] == "def hello():\n    print('Hello')"
    assert action_dict['new_string'] == "def hello():\n    print('Hello, World!')"
    assert action_dict['expected_replacements'] == 1


def test_gemini_write_file_action():
    """Test GeminiWriteFileAction."""
    action = GeminiWriteFileAction(
        file_path='/test/file.py',
        content="def hello():\n    print('Hello, World!')",
    )

    # Test to_dict method
    action_dict = action.to_dict()
    assert action_dict['file_path'] == '/test/file.py'
    assert action_dict['content'] == "def hello():\n    print('Hello, World!')"


def test_gemini_read_file_action():
    """Test GeminiReadFileAction."""
    # Test with all parameters
    action = GeminiReadFileAction(
        absolute_path='/test/file.py',
        offset=10,
        limit=20,
    )

    # Test to_dict method
    action_dict = action.to_dict()
    assert action_dict['absolute_path'] == '/test/file.py'
    assert action_dict['offset'] == 10
    assert action_dict['limit'] == 20

    # Test with only required parameters
    action = GeminiReadFileAction(
        absolute_path='/test/file.py',
    )

    # Test to_dict method
    action_dict = action.to_dict()
    assert action_dict['absolute_path'] == '/test/file.py'
    assert 'offset' not in action_dict
    assert 'limit' not in action_dict


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_replace(temp_dir, runtime_cls, run_as_openhands):
    """Test GeminiFileEditor replace functionality."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = "def hello():\n    print('Hello')\n    return None"

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'

        # Test replace using GeminiEditAction
        edit_action = GeminiEditAction(
            file_path=test_file,
            old_string="def hello():\n    print('Hello')",
            new_string="def hello():\n    print('Hello, World!')",
            expected_replacements=1,
        )
        obs = runtime.run_action(edit_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileEditObservation)

        # Verify the file was edited correctly
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileReadObservation)
        assert 'Hello, World!' in obs.content
        assert 'return None' in obs.content

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_replace_multiple_occurrences(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test GeminiFileEditor replace with multiple occurrences."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file with multiple occurrences
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = "print('Hello')\nprint('Hello')\nprint('Hello')"

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'

        # Test replace with expected_replacements=1 (should fail)
        edit_action = GeminiEditAction(
            file_path=test_file,
            old_string="print('Hello')",
            new_string="print('Hello, World!')",
            expected_replacements=1,
        )
        obs = runtime.run_action(edit_action)
        assert isinstance(obs, ErrorObservation)
        assert 'expected 1 occurrence(s) but found 3' in obs.content

        # Test replace with expected_replacements=3 (should succeed)
        edit_action = GeminiEditAction(
            file_path=test_file,
            old_string="print('Hello')",
            new_string="print('Hello, World!')",
            expected_replacements=3,
        )
        obs = runtime.run_action(edit_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileEditObservation)

        # Verify the file was edited correctly
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert 'Hello, World!' in obs.content
        assert obs.content.count('Hello, World!') == 3

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_replace_nonexistent_string(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test GeminiFileEditor replace with nonexistent string."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = "def hello():\n    print('Hello')\n    return None"

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'

        # Test replace with nonexistent string
        edit_action = GeminiEditAction(
            file_path=test_file,
            old_string='def goodbye():',
            new_string='def goodbye_world():',
            expected_replacements=1,
        )
        obs = runtime.run_action(edit_action)
        assert isinstance(obs, ErrorObservation)
        assert 'could not find the string to replace' in obs.content

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_write_file(temp_dir, runtime_cls, run_as_openhands):
    """Test GeminiFileEditor write_file functionality."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = "def hello():\n    print('Hello')\n    return None"

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileEditObservation)

        # Verify the file was created correctly
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileReadObservation)
        assert obs.content == content

        # Test overwriting the file
        new_content = "def hello_world():\n    print('Hello, World!')\n    return True"
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=new_content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileEditObservation)

        # Verify the file was overwritten correctly
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileReadObservation)
        assert obs.content == new_content

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_read_file(temp_dir, runtime_cls, run_as_openhands):
    """Test GeminiFileEditor read_file functionality."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file with multiple lines
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = '\n'.join([f'Line {i}' for i in range(1, 101)])

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'

        # Test reading the entire file
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileReadObservation)
        assert obs.content == content

        # Test reading with offset
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
            offset=50,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileReadObservation)
        assert 'Line 51' in obs.content
        assert 'Line 1' not in obs.content

        # Test reading with offset and limit
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
            offset=50,
            limit=10,
        )
        obs = runtime.run_action(read_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'
        assert isinstance(obs, FileReadObservation)
        assert 'Line 51' in obs.content
        assert 'Line 60' in obs.content
        assert 'Line 61' not in obs.content

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_read_nonexistent_file(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test GeminiFileEditor read_file with nonexistent file."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test reading a nonexistent file
        test_file = os.path.join(
            config.workspace_mount_path_in_sandbox, 'nonexistent.py'
        )
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
        )
        obs = runtime.run_action(read_action)
        assert isinstance(obs, ErrorObservation)
        assert 'File not found' in obs.content

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_read_with_invalid_offset(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test GeminiFileEditor read_file with invalid offset."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = 'Line 1\nLine 2\nLine 3'

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'

        # Test reading with negative offset
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
            offset=-1,
        )
        obs = runtime.run_action(read_action)
        assert isinstance(obs, ErrorObservation)
        assert 'Offset must be non-negative' in obs.content

        # Test reading with offset beyond file length
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
            offset=10,
        )
        obs = runtime.run_action(read_action)
        assert isinstance(obs, ErrorObservation)
        assert 'Offset 10 is out of range' in obs.content

    finally:
        _close_test_runtime(runtime)


@pytest.mark.skip(reason='Requires Docker runtime which is not available in CI')
def test_gemini_file_editor_read_with_invalid_limit(
    temp_dir, runtime_cls, run_as_openhands
):
    """Test GeminiFileEditor read_file with invalid limit."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.py')
        content = 'Line 1\nLine 2\nLine 3'

        # Create the file using GeminiWriteFileAction
        write_action = GeminiWriteFileAction(
            file_path=test_file,
            content=content,
        )
        obs = runtime.run_action(write_action)
        assert not isinstance(obs, ErrorObservation), f'Error: {obs.content}'

        # Test reading with negative limit
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
            offset=0,
            limit=-1,
        )
        obs = runtime.run_action(read_action)
        assert isinstance(obs, ErrorObservation)
        assert 'Limit must be positive' in obs.content

        # Test reading with zero limit
        read_action = GeminiReadFileAction(
            absolute_path=test_file,
            offset=0,
            limit=0,
        )
        obs = runtime.run_action(read_action)
        assert isinstance(obs, ErrorObservation)
        assert 'Limit must be positive' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_file_editor_create_action_from_tool_call():
    """Test create_action_from_tool_call method."""
    from openhands.llm.tool_names import (
        GEMINI_EDIT_TOOL_NAME,
        GEMINI_READ_FILE_TOOL_NAME,
        GEMINI_WRITE_FILE_TOOL_NAME,
    )

    # Test creating GeminiEditAction
    tool_args = {
        'file_path': '/test/file.py',
        'old_string': 'def hello():',
        'new_string': 'def hello_world():',
        'expected_replacements': 2,
    }
    action = GeminiFileEditor.create_action_from_tool_call(
        GEMINI_EDIT_TOOL_NAME, tool_args
    )
    assert isinstance(action, GeminiEditAction)
    assert action.file_path == '/test/file.py'
    assert action.old_string == 'def hello():'
    assert action.new_string == 'def hello_world():'
    assert action.expected_replacements == 2

    # Test creating GeminiWriteFileAction
    tool_args = {
        'file_path': '/test/file.py',
        'content': 'def hello_world():',
    }
    action = GeminiFileEditor.create_action_from_tool_call(
        GEMINI_WRITE_FILE_TOOL_NAME, tool_args
    )
    assert isinstance(action, GeminiWriteFileAction)
    assert action.file_path == '/test/file.py'
    assert action.content == 'def hello_world():'

    # Test creating GeminiReadFileAction
    tool_args = {
        'absolute_path': '/test/file.py',
        'offset': 10,
        'limit': 20,
    }
    action = GeminiFileEditor.create_action_from_tool_call(
        GEMINI_READ_FILE_TOOL_NAME, tool_args
    )
    assert isinstance(action, GeminiReadFileAction)
    assert action.absolute_path == '/test/file.py'
    assert action.offset == 10
    assert action.limit == 20

    # Test with unsupported tool name
    action = GeminiFileEditor.create_action_from_tool_call('unsupported_tool', {})
    assert action is None


def test_gemini_file_editor_get_supported_tool_names():
    """Test get_supported_tool_names method."""
    from openhands.llm.tool_names import (
        GEMINI_EDIT_TOOL_NAME,
        GEMINI_READ_FILE_TOOL_NAME,
        GEMINI_WRITE_FILE_TOOL_NAME,
    )

    tool_names = GeminiFileEditor.get_supported_tool_names()
    assert GEMINI_EDIT_TOOL_NAME in tool_names
    assert GEMINI_READ_FILE_TOOL_NAME in tool_names
    assert GEMINI_WRITE_FILE_TOOL_NAME in tool_names
    assert len(tool_names) == 3
