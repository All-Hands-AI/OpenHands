from unittest.mock import patch

from openhands.core.config import AppConfig
from openhands.io import read_input


def test_single_line_input():
    """Test that single line input works when cli_multiline_input is False"""
    config = AppConfig()
    config.cli_multiline_input = False

    with patch('builtins.input', return_value='hello world'):
        result = read_input(config.cli_multiline_input)
        assert result == 'hello world'


def test_multiline_input():
    """Test that multiline input works when cli_multiline_input is True"""
    config = AppConfig()
    config.cli_multiline_input = True

    # Simulate multiple lines of input followed by /exit
    mock_inputs = ['line 1', 'line 2', 'line 3', '/exit']

    with patch('builtins.input', side_effect=mock_inputs):
        result = read_input(config.cli_multiline_input)
        assert result == 'line 1\nline 2\nline 3'
