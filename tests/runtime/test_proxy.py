"""Tests for the HTTPS proxy functionality in ActionExecutor."""

import time
from pathlib import Path

import requests
from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation


def test_https_proxy(temp_dir, runtime_cls, run_as_openhands):
    """Test that the HTTPS proxy works correctly."""
    # Initialize runtime with HTTPS proxy
    runtime = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
        https_proxy_port=8443,
    )

    try:
        # Create a test file to serve
        test_file = Path(temp_dir) / 'test.txt'
        test_file.write_text('Hello from test server!')

        # Start a simple HTTP server on port 8000
        action = CmdRunAction(command='python3 -m http.server 8000 > server.log 2>&1 &')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0

        # Verify server is running
        action = CmdRunAction(command='sleep 3 && cat server.log')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0

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

        # Clean up test file and server log
        action = CmdRunAction(command='rm -rf test.txt server.log')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0

    finally:
        # Clean up runtime
        _close_test_runtime(runtime)
