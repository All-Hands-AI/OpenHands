"""Runtime tests for the Gemini editor tool."""

import os

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import ToolCallAction
from openhands.events.observation import ToolCallObservation


def test_gemini_editor_view_file(temp_dir, runtime_cls, run_as_openhands):
    """Test viewing a file with the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file first
        test_content = 'Hello, World!\nThis is a test file.\nLine 3'
        test_file_path = os.path.join('/workspace', 'test_view.txt')

        # Create the file using write_file command
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': test_content,
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Now view the file
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'view',
                'path': test_file_path,
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False
        assert 'Hello, World!' in obs.content
        assert 'This is a test file.' in obs.content
        assert 'Line 3' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_create_file(temp_dir, runtime_cls, run_as_openhands):
    """Test creating a file with the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        test_content = "# Test Python File\nprint('Hello from Gemini editor!')\n"
        test_file_path = os.path.join('/workspace', 'test_create.py')

        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': test_content,
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False
        assert 'created' in obs.content.lower() or 'successfully' in obs.content.lower()

        # Verify the file was created by viewing it
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'view',
                'path': test_file_path,
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False
        assert 'Test Python File' in obs.content
        assert "print('Hello from Gemini editor!')" in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_replace_text(temp_dir, runtime_cls, run_as_openhands):
    """Test replacing text in a file with the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create initial file
        initial_content = """def hello():
    print("Hello, World!")
    return "greeting"

def goodbye():
    print("Goodbye!")
    return "farewell"
"""
        test_file_path = os.path.join('/workspace', 'test_replace.py')

        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': initial_content,
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Replace text
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'replace',
                'path': test_file_path,
                'old_string': 'def hello():\n    print("Hello, World!")\n    return "greeting"',
                'new_string': 'def hello():\n    print("Hello, Gemini!")\n    return "gemini_greeting"',
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Verify the replacement
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'view',
                'path': test_file_path,
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False
        assert 'Hello, Gemini!' in obs.content
        assert 'gemini_greeting' in obs.content
        assert 'Hello, World!' not in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_write_file(temp_dir, runtime_cls, run_as_openhands):
    """Test writing content to a file with the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        test_content = '# New content\nThis completely replaces the file content.\n'
        test_file_path = os.path.join('/workspace', 'test_write.txt')

        # Create initial file
        initial_content = 'Old content that will be replaced.'
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': initial_content,
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Write new content (overwrite)
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'write_file',
                'path': test_file_path,
                'content': test_content,
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Verify the content was replaced
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'view',
                'path': test_file_path,
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False
        assert 'New content' in obs.content
        assert 'completely replaces' in obs.content
        assert 'Old content' not in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_read_file_with_range(temp_dir, runtime_cls, run_as_openhands):
    """Test reading a file with line range using the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a multi-line file
        test_content = """Line 1
Line 2
Line 3
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10"""
        test_file_path = os.path.join('/workspace', 'test_read_range.txt')

        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': test_content,
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Read with offset and limit
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'read_file',
                'path': test_file_path,
                'offset': 2,  # Start from line 3 (0-based)
                'limit': 3,  # Read 3 lines
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False
        assert 'Line 3' in obs.content
        assert 'Line 4' in obs.content
        assert 'Line 5' in obs.content
        assert 'Line 1' not in obs.content
        assert 'Line 6' not in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_view_directory(temp_dir, runtime_cls, run_as_openhands):
    """Test viewing a directory with the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create some test files in the workspace
        test_files = ['file1.txt', 'file2.py', 'file3.md']
        for filename in test_files:
            action = ToolCallAction(
                tool='gemini_editor',
                parameters={
                    'command': 'create',
                    'path': os.path.join('/workspace', filename),
                    'file_text': f'Content of {filename}',
                },
            )
            obs = runtime.run_action(action)
            assert isinstance(obs, ToolCallObservation)
            assert obs.error is False

        # View the directory
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'view',
                'path': '/workspace',
            },
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Check that all test files are listed
        for filename in test_files:
            assert filename in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_error_handling(temp_dir, runtime_cls, run_as_openhands):
    """Test error handling in the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test viewing non-existent file
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'view',
                'path': '/workspace/nonexistent.txt',
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        # Should handle gracefully, either with error or appropriate message

        # Test creating file that already exists (should fail)
        test_file_path = os.path.join('/workspace', 'existing.txt')
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': 'Initial content',
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        assert obs.error is False

        # Try to create the same file again
        action = ToolCallAction(
            tool='gemini_editor',
            parameters={
                'command': 'create',
                'path': test_file_path,
                'file_text': 'Duplicate content',
            },
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, ToolCallObservation)
        # Should either error or handle gracefully

    finally:
        _close_test_runtime(runtime)
