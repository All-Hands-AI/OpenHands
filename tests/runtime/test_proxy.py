"""Tests for the HTTPS proxy functionality in ActionExecutor."""

import http.server
import socketserver
import threading
import time
from pathlib import Path

import requests
from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation


def start_http_server(port):
    """Start a simple HTTP server in a separate thread."""
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(('', port), handler)

    def serve_forever():
        httpd.serve_forever()

    thread = threading.Thread(target=serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def test_https_proxy(temp_dir, runtime_cls, run_as_openhands):
    """Test that the HTTPS proxy works correctly."""
    # Initialize runtime with HTTPS proxy
    runtime = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
        https_proxy_port=8443,
    )

    # Create a test file to serve
    test_file = Path(temp_dir) / 'test.txt'
    test_file.write_text('Hello from test server!')

    # Start a simple HTTP server on port 8000
    http_server, server_thread = start_http_server(8000)

    try:
        # Give the proxy time to start
        time.sleep(2)

        # Configure the proxy settings for requests
        proxies = {
            'http': 'http://localhost:8443',
            'https': 'http://localhost:8443',
        }

        # Try to access the test server through the proxy
        response = requests.get(
            'http://localhost:8000/test.txt', proxies=proxies, verify=False
        )
        assert response.status_code == 200
        assert response.text == 'Hello from test server!'

        # Clean up test file
        action = CmdRunAction(command='rm -rf test.txt')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0

    finally:
        # Clean up server
        http_server.shutdown()
        http_server.server_close()
        server_thread.join(timeout=1)

        # Clean up runtime
        _close_test_runtime(runtime)
