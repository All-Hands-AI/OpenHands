import asyncio
import http.server
import socketserver
import threading
import time
from pathlib import Path

import pytest
import requests

from openhands.runtime.action_execution_server import ActionExecutor
from openhands.runtime.plugins import Plugin


def start_http_server(port):
    """Start a simple HTTP server in a separate thread"""
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)

    def serve_forever():
        httpd.serve_forever()

    thread = threading.Thread(target=serve_forever, daemon=True)
    thread.start()
    return httpd, thread


@pytest.mark.asyncio
async def test_https_proxy():
    # Create a temporary directory for the test
    work_dir = Path("/tmp/test_proxy")
    work_dir.mkdir(exist_ok=True)

    # Create a test file to serve
    test_file = work_dir / "test.txt"
    test_file.write_text("Hello from test server!")

    # Start a simple HTTP server on port 8000
    http_server, server_thread = start_http_server(8000)

    try:
        # Initialize ActionExecutor with HTTPS proxy
        executor = ActionExecutor(
            plugins_to_load=[],  # No plugins needed for this test
            work_dir=str(work_dir),
            username="openhands",
            user_id=1000,
            browsergym_eval_env=None,
            https_proxy_port=8443,
        )

        # Initialize the executor (this will start the proxy)
        await executor.ainit()

        # Give the proxy time to start
        time.sleep(2)

        # Configure the proxy settings for requests
        proxies = {
            "http": "http://localhost:8443",
            "https": "http://localhost:8443",
        }

        # Try to access the test server through the proxy
        response = requests.get("http://localhost:8000/test.txt", proxies=proxies, verify=False)
        assert response.status_code == 200
        assert response.text == "Hello from test server!"

    finally:
        # Clean up
        http_server.shutdown()
        http_server.server_close()
        server_thread.join(timeout=1)
        work_dir.unlink(missing_ok=True)