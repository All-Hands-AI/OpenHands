"""Integration tests for idle time updates."""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from openhands.runtime.utils.system_stats import (
    get_system_info,
    update_last_execution_time,
)
from openhands.server.routes.health import add_health_endpoints


@pytest.fixture
def app():
    """Create a test app."""
    app = FastAPI()
    add_health_endpoints(app)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_server_info_idle_time_increases_without_action(client):
    """Test that idle_time increases when no actions are executed."""
    # Reset the idle time
    update_last_execution_time()

    # Get initial server info
    initial_response = client.get('/server_info')
    initial_idle_time = initial_response.json()['idle_time']

    # Wait a bit
    time.sleep(0.2)

    # Get updated server info
    updated_response = client.get('/server_info')
    updated_idle_time = updated_response.json()['idle_time']

    # The idle time should have increased
    assert updated_idle_time > initial_idle_time
    assert (
        updated_idle_time >= initial_idle_time + 0.2
    )  # Should be at least the sleep time


def test_server_info_idle_time_resets_after_action():
    """Test that idle_time resets after an action is executed."""
    # Get initial server info
    initial_info = get_system_info()
    initial_idle_time = initial_info['idle_time']

    # Wait a bit
    time.sleep(0.2)

    # Simulate an action execution
    update_last_execution_time()

    # Get updated server info
    updated_info = get_system_info()
    updated_idle_time = updated_info['idle_time']

    # The idle time should have been reset
    assert updated_idle_time < initial_idle_time
    assert updated_idle_time < 0.1  # Should be very small


def test_multiple_server_info_requests_do_not_reset_idle_time(client):
    """Test that multiple server_info requests do not reset the idle time."""
    # Reset the idle time
    update_last_execution_time()

    # Wait a bit
    time.sleep(0.2)

    # Make multiple server_info requests
    for _ in range(3):
        client.get('/server_info')
        time.sleep(0.1)

    # Get server info
    response = client.get('/server_info')
    idle_time = response.json()['idle_time']

    # The idle time should be at least the total sleep time
    assert idle_time >= 0.5  # 0.2 + 3 * 0.1
