"""Tests for health endpoints."""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from openhands.server.routes.health import add_health_endpoints


def test_alive_endpoint():
    """Test that the /alive endpoint returns the expected response."""
    app = FastAPI()
    add_health_endpoints(app)
    client = TestClient(app)

    response = client.get('/alive')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_health_endpoint():
    """Test that the /health endpoint returns the expected response."""
    app = FastAPI()
    add_health_endpoints(app)
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.text == '"OK"'


@patch('openhands.server.routes.health.get_system_info')
def test_server_info_endpoint(mock_get_system_info):
    """Test that the /server_info endpoint returns the expected response."""
    # Mock the get_system_info function
    mock_system_info = {
        'uptime': 100.0,
        'idle_time': 10.0,
        'resources': {'cpu_percent': 5.0},
    }
    mock_get_system_info.return_value = mock_system_info

    # Create app and test client
    app = FastAPI()
    add_health_endpoints(app)
    client = TestClient(app)

    # Make request
    response = client.get('/server_info')

    # Verify response
    assert response.status_code == 200
    assert response.json() == mock_system_info

    # Verify get_system_info was called
    mock_get_system_info.assert_called_once()


@patch('openhands.runtime.utils.system_stats.update_last_execution_time')
def test_server_info_does_not_update_idle_time(mock_update_last_execution_time):
    """Test that the /server_info endpoint does not update the idle time."""
    # Create app and test client
    app = FastAPI()
    add_health_endpoints(app)
    client = TestClient(app)

    # Make request
    response = client.get('/server_info')

    # Verify response
    assert response.status_code == 200

    # Verify update_last_execution_time was not called
    mock_update_last_execution_time.assert_not_called()
