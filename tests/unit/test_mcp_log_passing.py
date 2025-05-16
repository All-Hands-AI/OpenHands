import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.runtime.action_execution_server import QueueHandler


class TestMCPLogPassing(unittest.TestCase):
    """Test the MCP log passing mechanism."""

    def test_queue_handler(self):
        """Test that the QueueHandler correctly captures logs."""
        from queue import Queue

        # Create a queue and handler
        log_queue = Queue()
        handler = QueueHandler(log_queue)
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))

        # Create a logger and add the handler
        logger = logging.getLogger('test_logger')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Log some messages
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')

        # Check that the messages were captured
        self.assertEqual(log_queue.qsize(), 4)
        self.assertEqual(log_queue.get(), 'DEBUG:test_logger:Debug message')
        self.assertEqual(log_queue.get(), 'INFO:test_logger:Info message')
        self.assertEqual(log_queue.get(), 'WARNING:test_logger:Warning message')
        self.assertEqual(log_queue.get(), 'ERROR:test_logger:Error message')

    @pytest.mark.asyncio
    async def test_update_mcp_server_log_capture(self):
        """Test that the update_mcp_server endpoint captures logs."""
        with patch(
            'openhands.runtime.action_execution_server.mcp_router'
        ) as mock_router:
            # Mock the router and its methods
            mock_router.profile_manager = MagicMock()
            mock_router.get_unique_servers = MagicMock(
                return_value=['server1', 'server2']
            )
            mock_router.update_servers = AsyncMock()

            # Mock the mcp_router_logger to simulate log messages
            with patch(
                'openhands.runtime.action_execution_server.mcp_router_logger'
            ) as mock_logger:
                # Set up the mock logger to emit a log message when addHandler is called
                def add_handler_side_effect(handler):
                    record = logging.LogRecord(
                        'mcpm.router.router',
                        logging.INFO,
                        '',
                        0,
                        'Connected to server jetbrains with capabilities',
                        (),
                        None,
                    )
                    handler.emit(record)

                    error_record = logging.LogRecord(
                        'mcpm.router.router',
                        logging.ERROR,
                        '',
                        0,
                        'Failed to add server jetbrains: No working IDE endpoint available',
                        (),
                        None,
                    )
                    handler.emit(error_record)

                mock_logger.addHandler.side_effect = add_handler_side_effect

                # Mock the request
                mock_request = MagicMock()
                mock_request.json = AsyncMock(return_value=[{'name': 'test_server'}])

                # Mock file operations
                with patch('builtins.open', MagicMock()):
                    with patch('json.load', MagicMock(return_value={'default': []})):
                        with patch('json.dump', MagicMock()):
                            with patch('os.path.exists', MagicMock(return_value=True)):
                                # Import the function to test
                                from openhands.runtime.action_execution_server import (
                                    update_mcp_server,
                                )

                                # Call the function
                                result = await update_mcp_server(mock_request)

                                # Check the result
                                self.assertEqual(result['status'], 'success')
                                self.assertEqual(
                                    result['servers_updated'], ['server1', 'server2']
                                )
                                self.assertEqual(len(result['logs']), 2)
                                self.assertIn(
                                    'Connected to server jetbrains', result['logs'][0]
                                )
                                self.assertIn(
                                    'Failed to add server jetbrains', result['logs'][1]
                                )


if __name__ == '__main__':
    unittest.main()
