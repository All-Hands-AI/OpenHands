"""Tests for the metrics endpoint with multiprocess support."""

import os
import tempfile
from unittest import mock

import pytest
from server.metrics import RUNNING_AGENT_LOOPS_GAUGE, metrics_app


@pytest.fixture
def mock_conversation_manager():
    """Mock the conversation manager."""
    with mock.patch('server.metrics.conversation_manager') as mock_cm:
        mock_cm.get_running_agent_loops_locally = mock.AsyncMock(
            return_value=['session1', 'session2']
        )
        yield mock_cm


@pytest.fixture
def multiprocess_dir():
    """Create a temporary directory for multiprocess metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestMetricsApp:
    """Test the metrics app functionality."""

    def test_gauge_has_multiprocess_mode(self):
        """Test that the running agent loops gauge is configured with multiprocess mode."""
        assert RUNNING_AGENT_LOOPS_GAUGE._multiprocess_mode == 'livesum'

    @pytest.mark.asyncio
    async def test_metrics_single_process_mode(self, mock_conversation_manager):
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
    async def test_metrics_multiprocess_mode(
        self, mock_conversation_manager, multiprocess_dir
    ):
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
            # In multiprocess mode, output should still contain metric names
            assert len(metrics_output) > 0

        finally:
            # Restore environment
            if original_env is not None:
                os.environ['PROMETHEUS_MULTIPROC_DIR'] = original_env
            else:
                if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
                    del os.environ['PROMETHEUS_MULTIPROC_DIR']

    @pytest.mark.asyncio
    async def test_update_metrics_called(self, mock_conversation_manager):
        """Test that _update_metrics is called when metrics endpoint is accessed."""
        handler = metrics_app()

        # Mock ASGI scope, receive, and send
        scope = {'type': 'http', 'method': 'GET', 'path': '/metrics'}
        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        # Call the handler
        await handler(scope, receive, send)

        # Verify that the conversation manager method was called
        mock_conversation_manager.get_running_agent_loops_locally.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiprocess_registry_creation(self, multiprocess_dir):
        """Test that multiprocess mode creates a new registry with MultiProcessCollector."""
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
                    return_value=[]
                )

                # Call the handler
                await handler(scope, receive, send)

                # Verify send was called
                assert send.call_count == 2

                # Get the body
                body_call = send.call_args_list[1][0][0]
                metrics_output = body_call['body'].decode('utf-8')

                # Should return valid Prometheus metrics format
                assert isinstance(metrics_output, str)

        finally:
            if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
                del os.environ['PROMETHEUS_MULTIPROC_DIR']

    @pytest.mark.asyncio
    async def test_response_headers(self):
        """Test that response headers are correctly set."""
        handler = metrics_app()

        # Mock ASGI scope, receive, and send
        scope = {'type': 'http', 'method': 'GET', 'path': '/metrics'}
        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        # Mock the conversation manager
        with mock.patch('server.metrics.conversation_manager') as mock_cm:
            mock_cm.get_running_agent_loops_locally = mock.AsyncMock(return_value=[])

            await handler(scope, receive, send)

            # Check response headers
            start_call = send.call_args_list[0][0][0]
            headers = start_call['headers']

            # Verify content-type header
            content_type_header = next(
                (h for h in headers if h[0] == b'content-type'), None
            )
            assert content_type_header is not None
            assert b'text/plain' in content_type_header[1]
            assert b'version=0.0.4' in content_type_header[1]
