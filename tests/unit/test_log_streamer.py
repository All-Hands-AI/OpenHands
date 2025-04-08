from unittest.mock import Mock

import pytest

from openhands.runtime.utils.log_streamer import LogStreamer


@pytest.fixture
def mock_container():
    return Mock()


@pytest.fixture
def mock_log_fn():
    return Mock()


def test_init_failure_handling(mock_container, mock_log_fn):
    """Test that LogStreamer handles initialization failures gracefully."""
    mock_container.logs.side_effect = Exception('Test error')

    streamer = LogStreamer(mock_container, mock_log_fn)
    assert streamer.stdout_thread is None
    assert streamer.log_generator is None
    mock_log_fn.assert_called_with(
        'error', 'Failed to initialize log streaming: Test error'
    )


def test_stream_logs_without_generator(mock_container, mock_log_fn):
    """Test that _stream_logs handles missing log generator gracefully."""
    streamer = LogStreamer(mock_container, mock_log_fn)
    streamer.log_generator = None
    streamer._stream_logs()
    mock_log_fn.assert_called_with('error', 'Log generator not initialized')


def test_cleanup_without_thread(mock_container, mock_log_fn):
    """Test that cleanup works even if stdout_thread is not initialized."""
    streamer = LogStreamer(mock_container, mock_log_fn)
    streamer.stdout_thread = None
    streamer.close()  # Should not raise any exceptions


def test_normal_operation(mock_container, mock_log_fn):
    """Test normal operation of LogStreamer."""
    mock_logs = iter([b'test log 1\n', b'test log 2\n'])
    mock_container.logs.return_value = mock_logs

    streamer = LogStreamer(mock_container, mock_log_fn)
    assert streamer.stdout_thread is not None
    assert streamer.log_generator is not None

    # Let the thread process the logs
    assert streamer.wait_for_completion(timeout=0.1)
    streamer.close()

    # Verify logs were processed
    expected_calls = [
        ('debug', '[inside container] test log 1'),
        ('debug', '[inside container] test log 2'),
    ]
    actual_calls = [(args[0], args[1]) for args, _ in mock_log_fn.call_args_list]
    for expected in expected_calls:
        assert expected in actual_calls


def test_del_without_thread(mock_container, mock_log_fn):
    """Test that __del__ works even if stdout_thread was not initialized."""
    streamer = LogStreamer(mock_container, mock_log_fn)
    delattr(
        streamer, 'stdout_thread'
    )  # Simulate case where the thread was never created
    streamer.__del__()  # Should not raise any exceptions
