import argparse
import os
import tempfile
from unittest.mock import patch

from openhands.core.config import OpenHandsConfig
from openhands.io import read_input, read_task, read_task_from_file


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


def test_read_task_with_file_option():
    """Test that read_task enhances file content with a prompt when using the file option."""
    # Create a temporary file with some content
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write('This is a test file content.')
        temp_file_path = temp_file.name

    try:
        # Create args with file option
        args = argparse.Namespace()
        args.file = temp_file_path
        args.task = None

        # Call the function with the args
        result = read_task(args, cli_multiline_input=False)

        # Check that the result contains the expected prompt structure
        assert f"The user has tagged a file '{temp_file_path}'" in result
        assert 'Please read and understand the following file content first:' in result
        assert 'This is a test file content.' in result
        assert (
            'After reviewing the file, please ask the user what they would like to do with it.'
            in result
        )
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
