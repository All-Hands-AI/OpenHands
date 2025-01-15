import unittest
from unittest.mock import Mock

from openhands.runtime.utils.log_streamer import LogStreamer


class TestLogStreamer(unittest.TestCase):
    def setUp(self):
        self.mock_container = Mock()
        self.mock_log_fn = Mock()

    def test_init_failure_handling(self):
        """Test that LogStreamer handles initialization failures gracefully."""
        self.mock_container.logs.side_effect = Exception('Test error')

        streamer = LogStreamer(self.mock_container, self.mock_log_fn)
        self.assertIsNone(streamer.stdout_thread)
        self.assertIsNone(streamer.log_generator)
        self.mock_log_fn.assert_called_with(
            'error', 'Failed to initialize log streaming: Test error'
        )

    def test_stream_logs_without_generator(self):
        """Test that _stream_logs handles missing log generator gracefully."""
        streamer = LogStreamer(self.mock_container, self.mock_log_fn)
        streamer.log_generator = None
        streamer._stream_logs()
        self.mock_log_fn.assert_called_with('error', 'Log generator not initialized')

    def test_cleanup_without_thread(self):
        """Test that cleanup works even if stdout_thread is not initialized."""
        streamer = LogStreamer(self.mock_container, self.mock_log_fn)
        streamer.stdout_thread = None
        streamer.close()  # Should not raise any exceptions

    def test_normal_operation(self):
        """Test normal operation of LogStreamer."""
        mock_logs = [b'test log 1\n', b'test log 2\n']
        self.mock_container.logs.return_value = mock_logs

        streamer = LogStreamer(self.mock_container, self.mock_log_fn)
        self.assertIsNotNone(streamer.stdout_thread)
        self.assertIsNotNone(streamer.log_generator)

        # Let the thread process the logs
        streamer.close()

        # Verify logs were processed
        expected_calls = [
            ('debug', '[inside container] test log 1'),
            ('debug', '[inside container] test log 2'),
        ]
        actual_calls = [
            (args[0], args[1]) for args, _ in self.mock_log_fn.call_args_list
        ]
        for expected in expected_calls:
            self.assertIn(expected, actual_calls)
