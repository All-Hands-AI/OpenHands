"""Runtime tests for Gemini-style file editing tools."""

import os

import pytest

from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
)
from openhands.runtime.plugins.agent_skills.gemini_file_editor.gemini_file_editor import (
    GeminiEditAction,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)

from .conftest import TEST_RUNTIME, _close_test_runtime, _load_runtime
from .docker_utils import is_docker_available

# Global variable to store Docker availability
DOCKER_AVAILABLE, DOCKER_ERROR_REASON = is_docker_available()

# Create a custom skip marker for Docker tests
docker_required = pytest.mark.skipif(
    not DOCKER_AVAILABLE, reason=f'Docker is not available: {DOCKER_ERROR_REASON}'
)


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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


@pytest.mark.skipif(TEST_RUNTIME != 'docker', reason='Test requires Docker runtime')
@docker_required
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
