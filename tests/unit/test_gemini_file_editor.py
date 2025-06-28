"""Unit tests for Gemini-style file editing tools."""

from openhands.events.action.gemini_file_editor import (
    GeminiEditAction,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)
from openhands.llm.tool_names import (
    GEMINI_EDIT_TOOL_NAME,
    GEMINI_READ_FILE_TOOL_NAME,
    GEMINI_WRITE_FILE_TOOL_NAME,
)
from openhands.runtime.plugins.agent_skills.gemini_file_editor.gemini_file_editor import (
    GeminiFileEditor,
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


def test_gemini_file_editor_create_action_from_tool_call():
    """Test create_action_from_tool_call method."""
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
    tool_names = GeminiFileEditor.get_supported_tool_names()
    assert GEMINI_EDIT_TOOL_NAME in tool_names
    assert GEMINI_READ_FILE_TOOL_NAME in tool_names
    assert GEMINI_WRITE_FILE_TOOL_NAME in tool_names
    assert len(tool_names) == 3
