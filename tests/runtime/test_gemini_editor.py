"""Runtime tests for the Gemini editor tool."""

import os

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import FileEditAction, FileReadAction
from openhands.events.event import FileEditSource
from openhands.events.observation import ErrorObservation, FileEditObservation, FileReadObservation


def test_gemini_editor_view_file(temp_dir, runtime_cls, run_as_openhands):
    """Test viewing a file with the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a test file first
        test_content = 'Hello, World!\nThis is a test file.\nLine 3'
        test_file_path = os.path.join('/workspace', 'test_view.txt')

        # Create the file using FileEditAction with create command
        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text=test_content,
            impl_source=FileEditSource.OH_ACI,
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileEditObservation)

        # Now view the file using FileReadAction
        action = FileReadAction(path=test_file_path)
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileReadObservation)
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

        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text=test_content,
            impl_source=FileEditSource.OH_ACI,
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileEditObservation)

        # Verify the file was created by reading it
        action = FileReadAction(path=test_file_path)
        obs = runtime.run_action(action)
        assert isinstance(obs, FileReadObservation)
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

        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text=initial_content,
            impl_source=FileEditSource.OH_ACI,
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, FileEditObservation)

        # Replace text using str_replace command
        action = FileEditAction(
            path=test_file_path,
            command='str_replace',
            old_str='def hello():\n    print("Hello, World!")\n    return "greeting"',
            new_str='def hello():\n    print("Hello, Gemini!")\n    return "gemini_greeting"',
            impl_source=FileEditSource.OH_ACI,
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileEditObservation)

        # Verify the replacement
        action = FileReadAction(path=test_file_path)
        obs = runtime.run_action(action)
        assert isinstance(obs, FileReadObservation)
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
        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text=initial_content,
            impl_source=FileEditSource.OH_ACI,
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, FileEditObservation)

        # Write new content (overwrite) using write command
        action = FileEditAction(
            path=test_file_path,
            command='write',
            content=test_content,
            impl_source=FileEditSource.OH_ACI,
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileEditObservation)

        # Verify the content was replaced
        action = FileReadAction(path=test_file_path)
        obs = runtime.run_action(action)
        assert isinstance(obs, FileReadObservation)
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

        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text=test_content,
            impl_source=FileEditSource.OH_ACI,
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, FileEditObservation)

        # Read with line range (start=3, end=5 for lines 3-5)
        action = FileReadAction(
            path=test_file_path,
            start=3,  # Start from line 3 (1-based)
            end=5,  # End at line 5 (1-based)
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileReadObservation)
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
            action = FileEditAction(
                path=os.path.join('/workspace', filename),
                command='create',
                file_text=f'Content of {filename}',
                impl_source=FileEditSource.OH_ACI,
            )
            obs = runtime.run_action(action)
            assert isinstance(obs, FileEditObservation)

        # View the directory using FileEditAction with view command
        action = FileEditAction(
            path='/workspace',
            command='view',
            impl_source=FileEditSource.OH_ACI,
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, FileEditObservation)

        # Check that all test files are listed
        for filename in test_files:
            assert filename in obs.content

    finally:
        _close_test_runtime(runtime)


def test_gemini_editor_error_handling(temp_dir, runtime_cls, run_as_openhands):
    """Test error handling in the Gemini editor."""
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test reading non-existent file
        action = FileReadAction(path='/workspace/nonexistent.txt')
        obs = runtime.run_action(action)
        # Should return an ErrorObservation for non-existent file
        assert isinstance(obs, ErrorObservation)
        assert 'File not found' in obs.content or 'No such file' in obs.content

        # Test creating file that already exists (should overwrite or handle gracefully)
        test_file_path = os.path.join('/workspace', 'existing.txt')
        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text='Initial content',
            impl_source=FileEditSource.OH_ACI,
        )
        obs = runtime.run_action(action)
        assert isinstance(obs, FileEditObservation)

        # Try to create the same file again
        action = FileEditAction(
            path=test_file_path,
            command='create',
            file_text='Duplicate content',
            impl_source=FileEditSource.OH_ACI,
        )
        obs = runtime.run_action(action)
        # Should either succeed (overwrite) or return an error
        assert isinstance(obs, (FileEditObservation, ErrorObservation))

    finally:
        _close_test_runtime(runtime)
