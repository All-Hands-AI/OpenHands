import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from openhands_aci.editor.editor import OHEditor
from openhands_aci.editor.exceptions import EditorToolParameterInvalidError


def test_file_editor_cwd_initialization():
    """Test that the OHEditor correctly initializes with a custom cwd."""
    test_cwd = "/tmp/test_cwd"
    editor = OHEditor(cwd=test_cwd)
    assert editor._cwd == test_cwd


def test_file_editor_cwd_default():
    """Test that the OHEditor uses os.getcwd() as the default cwd."""
    with mock.patch("os.getcwd", return_value="/mock/cwd"):
        editor = OHEditor()
        assert editor._cwd == "/mock/cwd"


def test_file_editor_validate_path_with_cwd():
    """Test that validate_path uses the custom cwd for path suggestions."""
    test_cwd = "/custom/cwd"
    editor = OHEditor(cwd=test_cwd)
    
    # Test with a relative path
    with pytest.raises(EditorToolParameterInvalidError) as excinfo:
        editor.validate_path("view", Path("relative/path"))
    
    # Check that the error message contains the correct suggested path
    assert f"{test_cwd}/relative/path" in str(excinfo.value)


def test_file_editor_in_action_execution_server():
    """Test that the OHEditor is initialized with the correct cwd in ActionExecutor."""
    from openhands.runtime.action_execution_server import ActionExecutor
    
    # Create a temporary directory to use as the working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize ActionExecutor with the temporary directory as the working directory
        executor = ActionExecutor(
            plugins_to_load=[],
            work_dir=temp_dir,
            username="test_user",
            user_id=1000,
            browsergym_eval_env=None,
        )
        
        # Check that the file_editor was initialized with the correct cwd
        assert executor.file_editor._cwd == temp_dir