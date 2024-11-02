import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent

from openhands.events import EventSource
from openhands.events.observation import FileEditObservation
from openhands.intent.watch import FileWatcher


@pytest.fixture
def mock_event_stream():
    """Create a mock event stream."""
    stream = MagicMock()
    stream.add_event = MagicMock()
    return stream


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def watcher(mock_event_stream, temp_dir):
    """Create a FileWatcher instance with mocked components."""
    with patch('watchdog.observers.Observer'):
        watcher = FileWatcher(temp_dir, mock_event_stream)
        yield watcher


def create_test_file(path: str, content: str = ""):
    """Create a test file with given content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def test_file_creation(watcher, temp_dir):
    """Test that file creation events are handled correctly."""
    file_path = os.path.join(temp_dir, "test.txt")
    content = "Hello, World!"
    
    # Create the file
    create_test_file(file_path, content)
    
    # Simulate watchdog event
    event = FileCreatedEvent(file_path)
    watcher.on_created(event)
    
    # Verify the event was emitted correctly
    watcher.event_stream.add_event.assert_called_once()
    args = watcher.event_stream.add_event.call_args[0]
    observation, source = args
    
    assert isinstance(observation, FileEditObservation)
    assert observation.path == "test.txt"  # Should be relative path
    assert observation.prev_exist is False
    assert observation.old_content == ""
    assert observation.new_content == content
    assert observation.content.startswith("+Hello, World!")
    assert source == EventSource.ENVIRONMENT


def test_file_modification(watcher, temp_dir):
    """Test that file modification events are handled correctly."""
    file_path = os.path.join(temp_dir, "test.txt")
    old_content = "Old content"
    new_content = "New content"
    
    # Create initial file
    create_test_file(file_path, old_content)
    watcher.file_contents[file_path] = old_content
    
    # Update the file
    create_test_file(file_path, new_content)
    
    # Simulate watchdog event
    event = FileModifiedEvent(file_path)
    watcher.on_modified(event)
    
    # Verify the event was emitted correctly
    watcher.event_stream.add_event.assert_called_once()
    observation, source = watcher.event_stream.add_event.call_args[0]
    
    assert isinstance(observation, FileEditObservation)
    assert observation.path == "test.txt"
    assert observation.prev_exist is True
    assert observation.old_content == old_content
    assert observation.new_content == new_content
    assert "-Old content" in observation.content
    assert "+New content" in observation.content
    assert source == EventSource.ENVIRONMENT


def test_file_deletion(watcher, temp_dir):
    """Test that file deletion events are handled correctly."""
    file_path = os.path.join(temp_dir, "test.txt")
    content = "Content to delete"
    
    # Create initial file
    create_test_file(file_path, content)
    watcher.file_contents[file_path] = content
    
    # Delete the file
    os.unlink(file_path)
    
    # Simulate watchdog event
    event = FileDeletedEvent(file_path)
    watcher.on_deleted(event)
    
    # Verify the event was emitted correctly
    watcher.event_stream.add_event.assert_called_once()
    observation, source = watcher.event_stream.add_event.call_args[0]
    
    assert isinstance(observation, FileEditObservation)
    assert observation.path == "test.txt"
    assert observation.prev_exist is True
    assert observation.old_content == content
    assert observation.new_content == ""
    assert "-Content to delete" in observation.content
    assert source == EventSource.ENVIRONMENT


def test_file_move(watcher, temp_dir):
    """Test that file move/rename events are handled correctly."""
    src_path = os.path.join(temp_dir, "old.txt")
    dst_path = os.path.join(temp_dir, "new.txt")
    content = "Content to move"
    
    # Create source file
    create_test_file(src_path, content)
    watcher.file_contents[src_path] = content
    
    # Move the file
    os.rename(src_path, dst_path)
    
    # Simulate watchdog event
    event = FileMovedEvent(src_path, dst_path)
    watcher.on_moved(event)
    
    # Should have two events: deletion and creation
    assert watcher.event_stream.add_event.call_count == 2
    
    # Check deletion event
    del_observation, del_source = watcher.event_stream.add_event.call_args_list[0][0]
    assert isinstance(del_observation, FileEditObservation)
    assert del_observation.path == "old.txt"
    assert del_observation.prev_exist is True
    assert del_observation.old_content == content
    assert del_observation.new_content == ""
    assert "-Content to move" in del_observation.content
    assert del_source == EventSource.ENVIRONMENT
    
    # Check creation event
    create_observation, create_source = watcher.event_stream.add_event.call_args_list[1][0]
    assert isinstance(create_observation, FileEditObservation)
    assert create_observation.path == "new.txt"
    assert create_observation.prev_exist is False
    assert create_observation.old_content == ""
    assert create_observation.new_content == content
    assert "+Content to move" in create_observation.content
    assert create_source == EventSource.ENVIRONMENT


def test_gitignore_handling(watcher, temp_dir):
    """Test that .gitignore patterns are respected."""
    # Create a .gitignore file
    gitignore_content = """
# Node modules
**/node_modules/
# Python
*.pyc
__pycache__/
# Custom
/ignored/
*.log
"""
    create_test_file(os.path.join(temp_dir, ".gitignore"), gitignore_content)
    
    # Reload gitignore patterns
    watcher.gitignore_spec = watcher._load_gitignore()
    
    # Test various paths
    test_cases = [
        ("node_modules/file.txt", True),
        ("frontend/node_modules/package.json", True),
        ("deep/path/node_modules/file.js", True),
        ("file.pyc", True),
        ("dir/__pycache__/module.pyc", True),
        ("ignored/file.txt", True),
        ("debug.log", True),
        ("src/app.js", False),
        ("frontend/src/components/Button.tsx", False),
        ("README.md", False),
    ]
    
    for rel_path, should_ignore in test_cases:
        abs_path = os.path.join(temp_dir, rel_path)
        assert watcher._should_ignore(abs_path) == should_ignore, f"Failed for {rel_path}"


def test_git_directory_ignored(watcher, temp_dir):
    """Test that .git directory is always ignored regardless of gitignore."""
    # Create some files in a .git directory
    git_files = [
        ".git/HEAD",
        ".git/config",
        ".git/refs/heads/main",
        ".git/objects/ab/cdef1234567890",
        "subdir/.git/HEAD",  # Test nested .git directories
        "subdir/.git/config",
    ]
    
    # Create the files
    for rel_path in git_files:
        abs_path = os.path.join(temp_dir, rel_path)
        create_test_file(abs_path, "test content")
    
    # Create some non-.git files for comparison
    normal_files = [
        "src/file.txt",
        "subdir/file.txt",
    ]
    for rel_path in normal_files:
        abs_path = os.path.join(temp_dir, rel_path)
        create_test_file(abs_path, "test content")
    
    # Test that all .git paths are ignored
    for rel_path in git_files:
        abs_path = os.path.join(temp_dir, rel_path)
        assert watcher._should_ignore(abs_path), f".git file not ignored: {rel_path}"
        
        # Also test the directory itself
        dir_path = os.path.dirname(abs_path)
        if '.git' in os.path.basename(dir_path):
            assert watcher._should_ignore(dir_path), f".git directory not ignored: {os.path.dirname(rel_path)}"
    
    # Test that normal files are not ignored
    for rel_path in normal_files:
        abs_path = os.path.join(temp_dir, rel_path)
        assert not watcher._should_ignore(abs_path), f"Non-.git file incorrectly ignored: {rel_path}"


def test_explicit_ignore_patterns(watcher, temp_dir):
    """Test that explicitly provided ignore patterns work."""
    # Create watcher with custom ignore patterns
    custom_patterns = ["*.txt", "temp/*"]
    with patch('watchdog.observers.Observer'):
        watcher = FileWatcher(
            temp_dir,
            watcher.event_stream,
            ignore_patterns=custom_patterns
        )
    
    test_cases = [
        ("file.txt", True),
        ("path/to/doc.txt", True),
        ("temp/any.js", True),
        ("temp/file.py", True),
        ("file.js", False),
        ("docs/file.md", False),
    ]
    
    for rel_path, should_ignore in test_cases:
        abs_path = os.path.join(temp_dir, rel_path)
        assert watcher._should_ignore(abs_path) == should_ignore, f"Failed for {rel_path}"


def test_watch_patterns(watcher, temp_dir):
    """Test that watch patterns work correctly."""
    # Create watcher with watch patterns
    watch_patterns = ["*.py", "src/*.ts"]
    with patch('watchdog.observers.Observer'):
        watcher = FileWatcher(
            temp_dir,
            watcher.event_stream,
            patterns=watch_patterns
        )
    
    test_cases = [
        ("file.py", True),
        ("src/app.ts", True),
        ("src/deep/file.ts", False),  # Not directly in src/
        ("file.js", False),
        ("src/file.js", False),
    ]
    
    for rel_path, should_watch in test_cases:
        abs_path = os.path.join(temp_dir, rel_path)
        assert watcher._should_watch(abs_path) == should_watch, f"Failed for {rel_path}"