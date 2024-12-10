import multiprocessing
import pytest
from unittest.mock import MagicMock, patch

from openhands.runtime.browser.browser_env import BrowserEnv
from openhands.core.exceptions import BrowserInitException


def test_browser_env_init():
    """Test that browser environment initialization doesn't produce duplicate messages."""
    with patch('openhands.runtime.browser.browser_env.logger') as mock_logger, \
         patch('multiprocessing.Process') as mock_process, \
         patch('multiprocessing.Pipe') as mock_pipe, \
         patch('gymnasium.make') as mock_gym_make:
        
        # Mock pipe
        mock_agent_side = MagicMock()
        mock_browser_side = MagicMock()
        mock_pipe.return_value = (mock_browser_side, mock_agent_side)
        mock_agent_side.poll.return_value = True
        mock_agent_side.recv.return_value = ('ALIVE', None)
        
        # Mock process
        mock_process.return_value.is_alive.return_value = True
        
        # Mock gym environment
        mock_env = MagicMock()
        mock_env.reset.return_value = ({}, {})
        mock_gym_make.return_value = mock_env
        
        # Mock browser process to log the start message
        def mock_browser_process():
            mock_logger.debug('Browser env started.')
            return True
        mock_process.return_value.target = mock_browser_process
        
        # Mock the browser process to actually call the target function
        def mock_start():
            mock_browser_process()
        mock_process.return_value.start = mock_start
        
        browser_env = BrowserEnv()
        
        # Verify that debug message is logged only once during initialization
        debug_calls = [call for call in mock_logger.debug.call_args_list if 'browser env' in str(call).lower()]
        assert len(debug_calls) == 1
        assert 'Browser env started' in str(debug_calls[0])

        browser_env.close()


def test_browser_env_init_failure():
    """Test that browser environment handles initialization failures correctly."""
    with patch('openhands.runtime.browser.browser_env.logger') as mock_logger, \
         patch('multiprocessing.Process') as mock_process, \
         patch('multiprocessing.Pipe') as mock_pipe:
        
        # Mock pipe
        mock_agent_side = MagicMock()
        mock_browser_side = MagicMock()
        mock_pipe.return_value = (mock_browser_side, mock_agent_side)
        mock_agent_side.poll.return_value = True
        mock_agent_side.recv.return_value = ('ALIVE', None)
        
        # Mock process failure
        mock_process.return_value.start.side_effect = Exception('Test error')
        
        with pytest.raises(Exception) as exc_info:
            BrowserEnv()
        
        assert 'Test error' in str(exc_info.value)


def test_browser_env_check_alive_failure():
    """Test that browser environment handles check_alive failures correctly."""
    with patch('openhands.runtime.browser.browser_env.logger') as mock_logger, \
         patch('multiprocessing.Process') as mock_process, \
         patch('multiprocessing.Pipe') as mock_pipe:
        
        # Mock pipe
        mock_agent_side = MagicMock()
        mock_browser_side = MagicMock()
        mock_pipe.return_value = (mock_browser_side, mock_agent_side)
        mock_agent_side.poll.return_value = False  # Simulate check_alive failure
        
        # Mock process
        mock_process.return_value.is_alive.return_value = True
        
        # Mock browser process to log the start message
        def mock_browser_process():
            mock_logger.debug('Browser env started.')
            return True
        mock_process.return_value.target = mock_browser_process
        
        # Mock the browser process to actually call the target function
        def mock_start():
            mock_browser_process()
        mock_process.return_value.start = mock_start
        
        # Mock tenacity retry decorator
        def mock_init_browser(self):
            try:
                self.process = multiprocessing.Process(target=self.browser_process)
                self.process.start()
            except Exception as e:
                logger.error(f'Failed to start browser process: {e}')
                raise
            
            if not self.check_alive():
                self.close()
                raise BrowserInitException('Failed to start browser environment.')
        
        with patch('openhands.runtime.browser.browser_env.BrowserEnv.init_browser', new=mock_init_browser):
            with pytest.raises(BrowserInitException) as exc_info:
                BrowserEnv()
            
            assert 'Failed to start browser environment' in str(exc_info.value)
