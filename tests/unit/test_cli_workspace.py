"""Test CLIRuntime class."""

import os
import tempfile

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.core.exceptions import LLMMalformedActionError
from openhands.events import EventStream
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def cli_runtime(temp_dir):
    """Create a CLIRuntime instance for testing."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('test', file_store)
    config = OpenHandsConfig()
    config.workspace_base = temp_dir
    runtime = CLIRuntime(config, event_stream)
    runtime._runtime_initialized = True  # Skip initialization
    return runtime


def test_sanitize_filename_valid_path(cli_runtime):
    """Test _sanitize_filename with a valid path."""
    test_path = os.path.join(cli_runtime._workspace_path, 'test.txt')
    sanitized_path = cli_runtime._sanitize_filename(test_path)
    assert sanitized_path == os.path.realpath(test_path)


def test_sanitize_filename_relative_path(cli_runtime):
    """Test _sanitize_filename with a relative path."""
    test_path = 'test.txt'
    expected_path = os.path.join(cli_runtime._workspace_path, test_path)
    sanitized_path = cli_runtime._sanitize_filename(test_path)
    assert sanitized_path == os.path.realpath(expected_path)


def test_sanitize_filename_outside_workspace(cli_runtime):
    """Test _sanitize_filename with a path outside the workspace."""
    test_path = '/tmp/test.txt'  # Path outside workspace
    with pytest.raises(LLMMalformedActionError) as exc_info:
        cli_runtime._sanitize_filename(test_path)
    assert 'Invalid path:' in str(exc_info.value)
    assert 'You can only work with files in' in str(exc_info.value)


def test_sanitize_filename_path_traversal(cli_runtime):
    """Test _sanitize_filename with path traversal attempt."""
    test_path = os.path.join(cli_runtime._workspace_path, '..', 'test.txt')
    with pytest.raises(LLMMalformedActionError) as exc_info:
        cli_runtime._sanitize_filename(test_path)
    assert 'Invalid path traversal:' in str(exc_info.value)
    assert 'Path resolves outside the workspace' in str(exc_info.value)


def test_sanitize_filename_absolute_path_with_dots(cli_runtime):
    """Test _sanitize_filename with absolute path containing dots."""
    test_path = os.path.join(cli_runtime._workspace_path, 'subdir', '..', 'test.txt')
    # Create the parent directory
    os.makedirs(os.path.join(cli_runtime._workspace_path, 'subdir'), exist_ok=True)
    sanitized_path = cli_runtime._sanitize_filename(test_path)
    assert sanitized_path == os.path.join(cli_runtime._workspace_path, 'test.txt')


def test_sanitize_filename_nested_path(cli_runtime):
    """Test _sanitize_filename with a nested path."""
    nested_dir = os.path.join(cli_runtime._workspace_path, 'dir1', 'dir2')
    os.makedirs(nested_dir, exist_ok=True)
    test_path = os.path.join(nested_dir, 'test.txt')
    sanitized_path = cli_runtime._sanitize_filename(test_path)
    assert sanitized_path == os.path.realpath(test_path)
