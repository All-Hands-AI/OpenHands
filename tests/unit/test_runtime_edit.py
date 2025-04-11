# tests/unit/test_runtime_edit.py
from unittest.mock import MagicMock

import pytest

from openhands.core.config import (  # Assuming AppConfig is needed
    AppConfig,
    SandboxConfig,
)
from openhands.events.action import FileEditAction, FileWriteAction
from openhands.events.event import FileEditSource
from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
)
from openhands.runtime.utils.edit import FileEditRuntimeMixin


# Mock AppConfig if necessary for FileEditRuntimeMixin initialization or methods
@pytest.fixture
def mock_config():
    config = MagicMock(spec=AppConfig)
    config.sandbox = MagicMock(spec=SandboxConfig)
    config.sandbox.enable_auto_lint = (
        False  # Disable linting for simplicity unless testing it
    )
    return config


# Create a dummy class that inherits the mixin for testing
class MockRuntime(FileEditRuntimeMixin):
    def __init__(self, config, *args, **kwargs):
        # Initialize FileEditRuntimeMixin part
        # Assuming enable_llm_editor=False as we are testing llm_diff_edit
        super().__init__(enable_llm_editor=False, *args, **kwargs)
        self.config = config
        # Mock essential methods used by llm_diff_edit
        self.read = MagicMock()
        self.write = MagicMock()
        # Mock _get_lint_error if linting is enabled in tests
        self._get_lint_error = MagicMock(return_value=None)

    # Implement abstract methods if FileEditRuntimeInterface requires them
    def run_ipython(self, action):
        pass

    # Add other abstract methods if needed


@pytest.fixture
def mock_runtime(mock_config):
    return MockRuntime(config=mock_config)


# Test cases for llm_diff_edit


def test_llm_diff_edit_exact_match(mock_runtime):
    action = FileEditAction(
        path='test.py',
        search="print('old')\nline2\n",
        replace="print('new')\nline2\n",
        impl_source=FileEditSource.LLM_DIFF,
    )
    original_content = "line0\nprint('old')\nline2\nline3\n"
    expected_new_content = "line0\nprint('new')\nline2\nline3\n"

    mock_runtime.read.return_value = FileReadObservation(
        content=original_content, path='test.py'
    )
    mock_runtime.write.return_value = FileWriteObservation(
        content='', path='test.py'
    )  # Assume write succeeds

    obs = mock_runtime.llm_diff_edit(action)

    assert isinstance(obs, FileEditObservation)
    assert obs.path == 'test.py'
    assert obs.old_content == original_content
    assert obs.new_content == expected_new_content
    mock_runtime.write.assert_called_once_with(
        FileWriteAction(path='test.py', content=expected_new_content)
    )


def test_llm_diff_edit_whitespace_flexible_match(mock_runtime):
    action = FileEditAction(
        path='test.py',
        search="  print('old')\n  line2\n",  # Search has 2 spaces
        replace="  print('new')\n  line2\n",  # Replace also has 2 spaces (relative indent)
        impl_source=FileEditSource.LLM_DIFF,
    )
    original_content = (
        "line0\n    print('old')\n    line2\nline3\n"  # Original has 4 spaces
    )
    expected_new_content = (
        "line0\n    print('new')\n    line2\nline3\n"  # Expect 4 spaces preserved
    )

    mock_runtime.read.return_value = FileReadObservation(
        content=original_content, path='test.py'
    )
    mock_runtime.write.return_value = FileWriteObservation(content='', path='test.py')

    obs = mock_runtime.llm_diff_edit(action)

    assert isinstance(obs, FileEditObservation)
    assert obs.new_content == expected_new_content
    mock_runtime.write.assert_called_once_with(
        FileWriteAction(path='test.py', content=expected_new_content)
    )


def test_llm_diff_edit_create_file(mock_runtime):
    action = FileEditAction(
        path='new_file.py',
        search='',  # Empty search for creation
        replace="print('hello new file')\n",
        impl_source=FileEditSource.LLM_DIFF,
    )
    original_content = ''  # File doesn't exist
    expected_new_content = "print('hello new file')\n"

    mock_runtime.read.return_value = ErrorObservation(
        content='File not found: new_file.py'
    )
    mock_runtime.write.return_value = FileWriteObservation(
        content='', path='new_file.py'
    )

    obs = mock_runtime.llm_diff_edit(action)

    assert isinstance(obs, FileEditObservation)
    assert obs.path == 'new_file.py'
    assert obs.old_content == original_content
    assert obs.new_content == expected_new_content
    assert obs.prev_exist is False
    mock_runtime.write.assert_called_once_with(
        FileWriteAction(path='new_file.py', content=expected_new_content)
    )


def test_llm_diff_edit_append_file(mock_runtime):
    action = FileEditAction(
        path='append.py',
        search='',  # Empty search for append
        replace="print('appended')\n",
        impl_source=FileEditSource.LLM_DIFF,
    )
    original_content = "print('original')\n"
    expected_new_content = "print('original')\nprint('appended')\n"

    mock_runtime.read.return_value = FileReadObservation(
        content=original_content, path='append.py'
    )
    mock_runtime.write.return_value = FileWriteObservation(content='', path='append.py')

    obs = mock_runtime.llm_diff_edit(action)

    assert isinstance(obs, FileEditObservation)
    assert obs.new_content == expected_new_content
    assert obs.prev_exist is True
    mock_runtime.write.assert_called_once_with(
        FileWriteAction(path='append.py', content=expected_new_content)
    )


def test_llm_diff_edit_no_match(mock_runtime):
    action = FileEditAction(
        path='test.py',
        search="print('not found')\n",
        replace="print('should not apply')\n",
        impl_source=FileEditSource.LLM_DIFF,
    )
    original_content = "print('something else')\n"

    mock_runtime.read.return_value = FileReadObservation(
        content=original_content, path='test.py'
    )

    obs = mock_runtime.llm_diff_edit(action)

    assert isinstance(obs, ErrorObservation)
    assert 'SEARCH block did not match' in obs.content
    assert 'FAILED SEARCH BLOCK' in obs.content
    assert "print('not found')" in obs.content
    mock_runtime.write.assert_not_called()  # Write should not be called on failure


def test_llm_diff_edit_create_file_non_empty_search_error(mock_runtime):
    action = FileEditAction(
        path='new_file.py',
        search='some search content',  # Non-empty search
        replace="print('hello new file')\n",
        impl_source=FileEditSource.LLM_DIFF,
    )

    mock_runtime.read.return_value = ErrorObservation(
        content='File not found: new_file.py'
    )

    obs = mock_runtime.llm_diff_edit(action)

    assert isinstance(obs, ErrorObservation)
    assert 'File new_file.py not found and SEARCH block is not empty' in obs.content
    mock_runtime.write.assert_not_called()


# TODO: Add tests for linting interaction if needed
