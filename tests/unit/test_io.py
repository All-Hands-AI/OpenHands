from unittest.mock import mock_open, patch

from openhands.core.config import OpenHandsConfig
from openhands.io import read_input, read_task_from_file


def test_single_line_input():
    """Test that single line input works when cli_multiline_input is False"""
    config = OpenHandsConfig()
    config.cli_multiline_input = False

    with patch('builtins.input', return_value='hello world'):
        result = read_input(config.cli_multiline_input)
        assert result == 'hello world'


def test_multiline_input():
    """Test that multiline input works when cli_multiline_input is True"""
    config = OpenHandsConfig()
    config.cli_multiline_input = True

    # Simulate multiple lines of input followed by /exit
    mock_inputs = ['line 1', 'line 2', 'line 3', '/exit']

    with patch('builtins.input', side_effect=mock_inputs):
        result = read_input(config.cli_multiline_input)
        assert result == 'line 1\nline 2\nline 3'


def test_read_task_from_file():
    """Test that read_task_from_file works correctly for regular files"""
    mock_content = 'This is a task from a file'

    with (
        patch('os.path.isdir', return_value=False),
        patch('builtins.open', mock_open(read_data=mock_content)),
    ):
        result = read_task_from_file('task.txt')
        assert result == mock_content


def test_read_task_from_file_directory_error():
    """Test that read_task_from_file raises IsADirectoryError when trying to read a directory"""
    with patch('os.path.isdir', return_value=True):
        try:
            read_task_from_file('/some/directory')
            raise AssertionError('Expected IsADirectoryError to be raised')
        except IsADirectoryError as e:
            assert 'is a directory, not a file' in str(e)
            assert '/some/directory' in str(e)
