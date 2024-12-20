"""Tests for the HTTPS proxy functionality in ActionExecutor."""

import os
import socket
import time
from pathlib import Path

import pytest
import requests

from openhands.runtime.utils.system import check_port_available


def test_check_port_available():
    """Test that check_port_available works correctly."""
    # Find a free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        _, free_port = s.getsockname()

    # Test that the port is available
    assert check_port_available(free_port)

    # Create a server to occupy the port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', free_port))
    server.listen(1)

    try:
        # Test that the port is no longer available
        assert not check_port_available(free_port)
    finally:
        server.close()
