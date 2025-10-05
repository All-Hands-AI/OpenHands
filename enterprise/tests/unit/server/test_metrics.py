"""Tests for the metrics endpoint with multiprocess support."""

import os
import tempfile
from unittest import mock

import pytest
from server.metrics import metrics_app


@pytest.fixture
def multiprocess_dir():
    """Create a temporary directory for multiprocess metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestMetricsApp:
    """Test the metrics app functionality."""

    @pytest.mark.asyncio
    async def test_metrics_single_process_mode(self):
        """Test metrics endpoint in single process mode (no PROMETHEUS_MULTIPROC_DIR)."""
        # Ensure PROMETHEUS_MULTIPROC_DIR is not set
        original_env = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
        if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
            del os.environ['PROMETHEUS_MULTIPROC_DIR']

        try:
            handler = metrics_app()

            # Mock ASGI scope, receive, and send
            scope = {'type': 'http', 'method': 'GET', 'path': '/metrics'}
            receive = mock.AsyncMock()
            send = mock.AsyncMock()

            # Mock the conversation manager
            with mock.patch('server.metrics.conversation_manager') as mock_cm:
                mock_cm.get_running_agent_loops_locally = mock.AsyncMock(
                    return_value=['session1', 'session2']
                )

                # Call the handler
                await handler(scope, receive, send)

                # Verify send was called twice (start + body)
                assert send.call_count == 2

                # Check the response start
                start_call = send.call_args_list[0][0][0]
                assert start_call['type'] == 'http.response.start'
                assert start_call['status'] == 200
                assert any(
                    header[0] == b'content-type' and b'text/plain' in header[1]
                    for header in start_call['headers']
                )

                # Check the response body
                body_call = send.call_args_list[1][0][0]
                assert body_call['type'] == 'http.response.body'
                assert isinstance(body_call['body'], bytes)

                # Verify metrics data contains expected content
                metrics_output = body_call['body'].decode('utf-8')
                assert 'saas_running_agent_loops' in metrics_output

        finally:
            # Restore environment
            if original_env is not None:
                os.environ['PROMETHEUS_MULTIPROC_DIR'] = original_env

    @pytest.mark.asyncio
    async def test_metrics_multiprocess_mode(self, multiprocess_dir):
        """Test metrics endpoint in multiprocess mode (with PROMETHEUS_MULTIPROC_DIR)."""
        # Set PROMETHEUS_MULTIPROC_DIR
        original_env = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
        os.environ['PROMETHEUS_MULTIPROC_DIR'] = multiprocess_dir

        try:
            handler = metrics_app()

            # Mock ASGI scope, receive, and send
            scope = {'type': 'http', 'method': 'GET', 'path': '/metrics'}
            receive = mock.AsyncMock()
            send = mock.AsyncMock()

            # Mock the conversation manager to avoid actual calls
            with mock.patch('server.metrics.conversation_manager') as mock_cm:
                mock_cm.get_running_agent_loops_locally = mock.AsyncMock(
                    return_value=['test_session']
                )

                # Call the handler
                await handler(scope, receive, send)

                # Verify send was called twice (start + body)
                assert send.call_count == 2

                # Check the response start
                start_call = send.call_args_list[0][0][0]
                assert start_call['type'] == 'http.response.start'
                assert start_call['status'] == 200

                # Check the response body
                body_call = send.call_args_list[1][0][0]
                assert body_call['type'] == 'http.response.body'
                assert isinstance(body_call['body'], bytes)

                # Verify metrics data is returned
                metrics_output = body_call['body'].decode('utf-8')
                # In multiprocess mode, metrics are collected from files in the directory
                # The output should be a valid string (might be empty if no files exist yet)
                assert isinstance(metrics_output, str)

        finally:
            # Restore environment
            if original_env is not None:
                os.environ['PROMETHEUS_MULTIPROC_DIR'] = original_env
            else:
                if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
                    del os.environ['PROMETHEUS_MULTIPROC_DIR']
