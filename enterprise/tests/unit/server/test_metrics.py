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
        """Test metrics endpoint aggregates data from multiple simulated processes."""
        import subprocess
        import sys
        from prometheus_client import CollectorRegistry
        from prometheus_client import multiprocess

        # Set PROMETHEUS_MULTIPROC_DIR before running subprocess
        original_env = os.environ.get('PROMETHEUS_MULTIPROC_DIR')
        os.environ['PROMETHEUS_MULTIPROC_DIR'] = multiprocess_dir

        try:
            # Simulate multiple worker processes by running subprocess that writes metrics
            # Each subprocess writes metrics to the multiprocess directory
            worker_script = f'''
import os
os.environ['PROMETHEUS_MULTIPROC_DIR'] = '{multiprocess_dir}'
from prometheus_client import Gauge

worker_gauge = Gauge(
    'test_worker_metric',
    'Test metric from worker',
    ['worker_id'],
    multiprocess_mode='livesum',
)
worker_gauge.labels(worker_id='worker{{}}').set({{}})
'''
            # Run 3 "worker processes" that each write metrics
            for i in range(1, 4):
                result = subprocess.run(
                    [sys.executable, '-c', worker_script.format(i, i * 10)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f'Worker {i} failed: {result.stderr}'
                    )

            # Now collect metrics using MultiProcessCollector
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)

            from prometheus_client import generate_latest

            metrics_output = generate_latest(registry).decode('utf-8')

            # Verify that metrics from all workers are present
            assert 'test_worker_metric' in metrics_output
            assert 'worker_id="worker1"' in metrics_output
            assert 'worker_id="worker2"' in metrics_output
            assert 'worker_id="worker3"' in metrics_output

            # Verify the values are present (livesum aggregation)
            assert '10.0' in metrics_output or '10' in metrics_output
            assert '20.0' in metrics_output or '20' in metrics_output
            assert '30.0' in metrics_output or '30' in metrics_output

            # Now test the actual metrics_app() handler with multiprocess mode
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

            with mock.patch('server.metrics.conversation_manager') as mock_cm:
                mock_cm.get_running_agent_loops_locally = mock.AsyncMock(
                    return_value=['session1', 'session2']
                )

                await handler(scope, receive, send)

                assert send.call_count == 2

                start_call = send.call_args_list[0][0][0]
                assert start_call['type'] == 'http.response.start'
                assert start_call['status'] == 200

                body_call = send.call_args_list[1][0][0]
                assert body_call['type'] == 'http.response.body'
                assert isinstance(body_call['body'], bytes)

                app_metrics_output = body_call['body'].decode('utf-8')
                # Should contain our test metrics from multiple workers
                assert 'test_worker_metric' in app_metrics_output
                # Verify multiprocess aggregation worked - all 3 workers present
                assert 'worker_id="worker1"' in app_metrics_output
                assert 'worker_id="worker2"' in app_metrics_output
                assert 'worker_id="worker3"' in app_metrics_output

        finally:
            # Restore environment
            if original_env is not None:
                os.environ['PROMETHEUS_MULTIPROC_DIR'] = original_env
            else:
                if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
                    del os.environ['PROMETHEUS_MULTIPROC_DIR']
