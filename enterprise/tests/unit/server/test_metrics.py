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
            scope = {
                'type': 'http',
                'method': 'GET',
                'path': '/metrics',
                'headers': [],
                'query_string': b'',
            }
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
        """Test that our app's metrics are aggregated from multiple worker processes."""
        import subprocess
        import sys

        # Set PROMETHEUS_MULTIPROC_DIR before running subprocess
        original_env = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
        os.environ['PROMETHEUS_MULTIPROC_DIR'] = multiprocess_dir

        try:
            # Simulate 3 uvicorn worker processes, each tracking different sessions
            # Each worker imports the actual RUNNING_AGENT_LOOPS_GAUGE from our app
            worker_script = f'''
import os
os.environ['PROMETHEUS_MULTIPROC_DIR'] = '{multiprocess_dir}'

# Import the actual gauge from our application code
from server.metrics import RUNNING_AGENT_LOOPS_GAUGE

# Simulate this worker tracking specific sessions
sessions = {{}}
for session_id in sessions:
    RUNNING_AGENT_LOOPS_GAUGE.labels(session_id=session_id).set(1)
'''
            # Worker 1 tracks sessions: session1, session2
            result = subprocess.run(
                [sys.executable, '-c', worker_script.format(['session1', 'session2'])],
                capture_output=True,
                text=True,
                cwd='/workspace/OpenHands/enterprise',
            )
            if result.returncode != 0:
                raise RuntimeError(f'Worker 1 failed: {result.stderr}')

            # Worker 2 tracks sessions: session3, session4
            result = subprocess.run(
                [sys.executable, '-c', worker_script.format(['session3', 'session4'])],
                capture_output=True,
                text=True,
                cwd='/workspace/OpenHands/enterprise',
            )
            if result.returncode != 0:
                raise RuntimeError(f'Worker 2 failed: {result.stderr}')

            # Worker 3 tracks sessions: session5
            result = subprocess.run(
                [sys.executable, '-c', worker_script.format(['session5'])],
                capture_output=True,
                text=True,
                cwd='/workspace/OpenHands/enterprise',
            )
            if result.returncode != 0:
                raise RuntimeError(f'Worker 3 failed: {result.stderr}')

            # Now test that our metrics_app() handler aggregates all sessions from all workers
            handler = metrics_app()

            scope = {
                'type': 'http',
                'method': 'GET',
                'path': '/metrics',
                'headers': [],
                'query_string': b'',
            }
            receive = mock.AsyncMock()
            send = mock.AsyncMock()

            # Mock conversation_manager to not interfere with our test
            with mock.patch('server.metrics.conversation_manager') as mock_cm:
                mock_cm.get_running_agent_loops_locally = mock.AsyncMock(
                    return_value=[]
                )

                await handler(scope, receive, send)

                assert send.call_count == 2

                start_call = send.call_args_list[0][0][0]
                assert start_call['type'] == 'http.response.start'
                assert start_call['status'] == 200

                body_call = send.call_args_list[1][0][0]
                assert body_call['type'] == 'http.response.body'
                assert isinstance(body_call['body'], bytes)

                metrics_output = body_call['body'].decode('utf-8')

                # Verify our app's metric is present
                assert 'saas_running_agent_loops' in metrics_output

                # Verify all sessions from all 3 workers are aggregated
                # This proves multiprocess mode is working correctly
                assert 'session_id="session1"' in metrics_output
                assert 'session_id="session2"' in metrics_output
                assert 'session_id="session3"' in metrics_output
                assert 'session_id="session4"' in metrics_output
                assert 'session_id="session5"' in metrics_output

        finally:
            # Restore environment
            if original_env is not None:
                os.environ['PROMETHEUS_MULTIPROC_DIR'] = original_env
            else:
                if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
                    del os.environ['PROMETHEUS_MULTIPROC_DIR']
