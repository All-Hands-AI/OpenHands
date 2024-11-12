import pytest
from unittest.mock import MagicMock, patch

from openhands.runtime.browser.browser_env import BrowserEnv


@patch('multiprocessing.Process')
@patch('multiprocessing.Pipe')
def test_browser_env_reset(mock_pipe, mock_process):
    """Test that the browser environment resets properly."""
    # Mock the pipe
    mock_agent_side = MagicMock()
    mock_browser_side = MagicMock()
    mock_pipe.return_value = (mock_browser_side, mock_agent_side)
    
    # Mock the process
    mock_process_instance = MagicMock()
    mock_process.return_value = mock_process_instance
    mock_process_instance.is_alive.return_value = True
    
    # Mock the pipe response for alive check and reset
    mock_agent_side.poll.side_effect = [True, True]  # First for alive check, second for reset
    mock_agent_side.recv.side_effect = [
        ('ALIVE', None),  # Response for alive check
        (None, {'text_content': 'test', 'screenshot': 'test'}),  # Response for reset
    ]

    # Create browser environment
    browser_env = BrowserEnv()

    # Reset the environment
    obs = browser_env.reset()

    # Verify that reset was called
    mock_agent_side.send.assert_called_with(('RESET', None))

    # Verify that the environment has been reset
    assert obs is not None
    assert 'text_content' in obs
    assert 'screenshot' in obs

    # Clean up
    browser_env.close()
