"""Tests for the metrics endpoint with multiprocess support."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from server.metrics import metrics_app


def get_enterprise_dir():
    """Get the enterprise directory path relative to this test file."""
    # This test file is at: enterprise/tests/unit/server/test_metrics.py
    # Enterprise directory is at: enterprise/
    # Path calculation: server/ -> unit/ -> tests/ -> enterprise/
    # So we need to go up 4 levels: ../../../../
    return Path(__file__).parent.parent.parent.parent


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
            with mock.patch('openhands.server.shared.conversation_manager') as mock_cm:
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
            # Simulate 3 uvicorn worker processes, each running actual app code
            # Each worker calls _update_metrics() with a real ClusteredConversationManager instance
            # Using triple braces {{{}}} to escape the f-string interpolation
            worker_script_template = f"""
import os
import sys

# CRITICAL: Set PROMETHEUS_MULTIPROC_DIR BEFORE any prometheus_client imports
os.environ['PROMETHEUS_MULTIPROC_DIR'] = '{multiprocess_dir}'

# Now safe to import
import asyncio

# Import the actual app code and classes
from server.metrics import _update_metrics, RUNNING_AGENT_LOOPS_GAUGE
from server.clustered_conversation_manager import ClusteredConversationManager
import openhands.server.shared

# Debug prometheus_client mode
from prometheus_client import values
print(f"Prometheus ValueClass: {{values.ValueClass}}", flush=True)
print(f"PROMETHEUS_MULTIPROC_DIR={{os.environ.get('PROMETHEUS_MULTIPROC_DIR')}}", flush=True)
print(f"Gauge type: {{type(RUNNING_AGENT_LOOPS_GAUGE)}}", flush=True)

# Create a minimal ClusteredConversationManager instance for testing
async def run_worker():
    sessions = SESSIONS_PLACEHOLDER

    # Get the current conversation_manager (StandaloneConversationManager)
    base_cm = openhands.server.shared.conversation_manager

    # Create a real ClusteredConversationManager that inherits all properties
    # but adds get_running_agent_loops_locally
    class TestClusteredConversationManager(ClusteredConversationManager):
        async def get_running_agent_loops_locally(self):
            return sessions

    # Create instance with same properties as base_cm
    test_cm = TestClusteredConversationManager(
        sio=base_cm.sio,
        config=base_cm.config,
        file_store=base_cm.file_store,
        server_config=base_cm.server_config,
        monitoring_listener=base_cm.monitoring_listener,
    )

    # Temporarily replace conversation_manager
    original_cm = openhands.server.shared.conversation_manager
    openhands.server.shared.conversation_manager = test_cm

    try:
        await _update_metrics()
    finally:
        openhands.server.shared.conversation_manager = original_cm

asyncio.run(run_worker())
"""
            # Worker 1 tracks sessions: session1, session2
            worker1_script = worker_script_template.replace(
                'SESSIONS_PLACEHOLDER', str(['session1', 'session2'])
            )
            result = subprocess.run(
                [sys.executable, '-W', 'ignore', '-c', worker1_script],
                capture_output=True,
                text=True,
                cwd=str(get_enterprise_dir()),
            )
            print(f'Worker 1 stdout: {result.stdout}')
            print(f'Worker 1 stderr: {result.stderr[:500] if result.stderr else ""}')
            if result.returncode != 0:
                raise RuntimeError(
                    f'Worker 1 failed with code {result.returncode}\n'
                    f'stdout: {result.stdout}\nstderr: {result.stderr}'
                )

            # Worker 2 tracks sessions: session3, session4
            worker2_script = worker_script_template.replace(
                'SESSIONS_PLACEHOLDER', str(['session3', 'session4'])
            )
            result = subprocess.run(
                [sys.executable, '-W', 'ignore', '-c', worker2_script],
                capture_output=True,
                text=True,
                cwd=str(get_enterprise_dir()),
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f'Worker 2 failed with code {result.returncode}\n'
                    f'stdout: {result.stdout}\nstderr: {result.stderr}'
                )

            # Worker 3 tracks sessions: session5
            worker3_script = worker_script_template.replace(
                'SESSIONS_PLACEHOLDER', str(['session5'])
            )
            result = subprocess.run(
                [sys.executable, '-W', 'ignore', '-c', worker3_script],
                capture_output=True,
                text=True,
                cwd=str(get_enterprise_dir()),
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f'Worker 3 failed with code {result.returncode}\n'
                    f'stdout: {result.stdout}\nstderr: {result.stderr}'
                )

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
