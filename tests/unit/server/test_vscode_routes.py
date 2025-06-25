"""Unit tests for VSCode server routes

Tests the VSCode integration API endpoints that implement the Lazy Connection Pattern.
Covers registration, discovery, heartbeat, and management functionality.
"""

import json
import time
from unittest.mock import patch
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from fastapi import status as http_status

from openhands.server.routes.vscode import app, _vscode_registry, VSCodeInstance


@pytest.fixture
def client():
    """Create a test client for the VSCode routes."""
    return TestClient(app)


@pytest.fixture
def clean_registry():
    """Clean the VSCode registry before and after each test."""
    _vscode_registry.clear()
    yield
    _vscode_registry.clear()


@pytest.fixture
def sample_registration_data():
    """Sample data for VSCode registration requests."""
    return {
        "workspace_path": "/home/user/project",
        "workspace_name": "test-project",
        "vscode_version": "1.85.0",
        "extension_version": "0.1.0",
        "capabilities": ["file_operations", "terminal_access"]
    }


@pytest.fixture
def mock_time():
    """Mock time.time() to return predictable values."""
    with patch('time.time', return_value=1234567890.0):
        yield 1234567890.0


class TestVsCodeRegistration:
    """Test VSCode instance registration endpoint."""
    
    def test_register_vscode_instance_success(self, client, clean_registry, sample_registration_data, mock_time):
        """Test successful VSCode instance registration."""
        response = client.post("/register", json=sample_registration_data)
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        
        # Check response structure
        assert "connection_id" in data
        assert "message" in data
        assert data["message"] == "Successfully registered VSCode instance for workspace 'test-project'"
        
        # Verify connection_id is a valid UUID format
        connection_id = data["connection_id"]
        assert len(connection_id) == 36  # UUID length
        assert connection_id.count('-') == 4  # UUID format
        
        # Verify instance was stored in registry
        assert connection_id in _vscode_registry
        instance = _vscode_registry[connection_id]
        assert instance.workspace_path == sample_registration_data["workspace_path"]
        assert instance.workspace_name == sample_registration_data["workspace_name"]
        assert instance.vscode_version == sample_registration_data["vscode_version"]
        assert instance.extension_version == sample_registration_data["extension_version"]
        assert instance.capabilities == sample_registration_data["capabilities"]
        assert instance.status == "active"
        assert instance.registered_at == mock_time
        assert instance.last_heartbeat == mock_time

    def test_register_vscode_instance_minimal_data(self, client, clean_registry, mock_time):
        """Test registration with minimal required data."""
        minimal_data = {
            "workspace_path": "/home/user/minimal",
            "workspace_name": "minimal-project",
            "vscode_version": "1.85.0",
            "extension_version": "0.1.0"
            # capabilities is optional and should default to empty list
        }
        
        response = client.post("/register", json=minimal_data)
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        connection_id = data["connection_id"]
        
        # Verify instance was stored with default capabilities
        instance = _vscode_registry[connection_id]
        assert instance.capabilities == []

    def test_register_vscode_instance_missing_required_fields(self, client, clean_registry):
        """Test registration with missing required fields."""
        incomplete_data = {
            "workspace_path": "/home/user/project",
            # Missing workspace_name, vscode_version, extension_version
        }
        
        response = client.post("/register", json=incomplete_data)
        
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        # Verify no instance was stored
        assert len(_vscode_registry) == 0

    def test_register_vscode_instance_invalid_json(self, client, clean_registry):
        """Test registration with invalid JSON data."""
        response = client.post("/register", data="invalid json")
        
        assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
        # Verify no instance was stored
        assert len(_vscode_registry) == 0

    def test_register_vscode_instance_empty_capabilities(self, client, clean_registry, mock_time):
        """Test registration with explicitly empty capabilities."""
        data_with_empty_capabilities = {
            "workspace_path": "/home/user/project",
            "workspace_name": "test-project",
            "vscode_version": "1.85.0",
            "extension_version": "0.1.0",
            "capabilities": []
        }
        
        response = client.post("/register", json=data_with_empty_capabilities)
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        connection_id = data["connection_id"]
        
        # Verify instance was stored with empty capabilities
        instance = _vscode_registry[connection_id]
        assert instance.capabilities == []


class TestVsCodeDiscovery:
    """Test VSCode instance discovery endpoint."""
    
    def test_get_vscode_instances_empty_registry(self, client, clean_registry):
        """Test discovery when no instances are registered."""
        response = client.get("/instances")
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_get_vscode_instances_single_instance(self, client, clean_registry, mock_time):
        """Test discovery with a single registered instance."""
        # Register an instance first
        registration_data = {
            "workspace_path": "/home/user/project",
            "workspace_name": "test-project",
            "vscode_version": "1.85.0",
            "extension_version": "0.1.0",
            "capabilities": ["file_operations"]
        }
        
        reg_response = client.post("/register", json=registration_data)
        connection_id = reg_response.json()["connection_id"]
        
        # Now test discovery
        response = client.get("/instances")
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        
        instance_info = data[0]
        assert instance_info["connection_id"] == connection_id
        assert instance_info["workspace_name"] == "test-project"
        assert instance_info["workspace_path"] == "/home/user/project"
        assert instance_info["status"] == "active"
        assert instance_info["registered_at"] == mock_time
        assert instance_info["last_heartbeat"] == mock_time

    def test_get_vscode_instances_multiple_instances(self, client, clean_registry, mock_time):
        """Test discovery with multiple registered instances."""
        # Register multiple instances
        instances_data = [
            {
                "workspace_path": "/home/user/project1",
                "workspace_name": "project-1",
                "vscode_version": "1.85.0",
                "extension_version": "0.1.0",
                "capabilities": ["file_operations"]
            },
            {
                "workspace_path": "/home/user/project2",
                "workspace_name": "project-2",
                "vscode_version": "1.86.0",
                "extension_version": "0.2.0",
                "capabilities": ["terminal_access"]
            }
        ]
        
        connection_ids = []
        for instance_data in instances_data:
            reg_response = client.post("/register", json=instance_data)
            connection_ids.append(reg_response.json()["connection_id"])
        
        # Test discovery
        response = client.get("/instances")
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        
        # Verify both instances are returned
        returned_ids = [instance["connection_id"] for instance in data]
        assert set(returned_ids) == set(connection_ids)
        
        # Verify instance details
        for instance_info in data:
            if instance_info["workspace_name"] == "project-1":
                assert instance_info["workspace_path"] == "/home/user/project1"
            elif instance_info["workspace_name"] == "project-2":
                assert instance_info["workspace_path"] == "/home/user/project2"

    def test_get_vscode_instances_stale_cleanup(self, client, clean_registry):
        """Test that stale instances are cleaned up during discovery."""
        current_time = 1234567890.0
        stale_time = current_time - (6 * 60)  # 6 minutes ago (stale threshold is 5 minutes)
        
        # Manually add a stale instance to registry
        stale_connection_id = "stale-instance-id"
        _vscode_registry[stale_connection_id] = VSCodeInstance(
            connection_id=stale_connection_id,
            workspace_path="/home/user/stale",
            workspace_name="stale-project",
            vscode_version="1.85.0",
            extension_version="0.1.0",
            capabilities=[],
            registered_at=stale_time,
            last_heartbeat=stale_time,
            status="active"
        )
        
        # Add a fresh instance
        with patch('time.time', return_value=current_time):
            registration_data = {
                "workspace_path": "/home/user/fresh",
                "workspace_name": "fresh-project",
                "vscode_version": "1.85.0",
                "extension_version": "0.1.0"
            }
            reg_response = client.post("/register", json=registration_data)
            fresh_connection_id = reg_response.json()["connection_id"]
        
        # Verify both instances are in registry before discovery
        assert len(_vscode_registry) == 2
        assert stale_connection_id in _vscode_registry
        assert fresh_connection_id in _vscode_registry
        
        # Test discovery - should clean up stale instance
        with patch('time.time', return_value=current_time):
            response = client.get("/instances")
        
        assert response.status_code == http_status.HTTP_200_OK
        data = response.json()
        
        # Only fresh instance should be returned
        assert len(data) == 1
        assert data[0]["connection_id"] == fresh_connection_id
        assert data[0]["workspace_name"] == "fresh-project"
        
        # Verify stale instance was removed from registry
        assert len(_vscode_registry) == 1
        assert stale_connection_id not in _vscode_registry
        assert fresh_connection_id in _vscode_registry


if __name__ == "__main__":
    pytest.main([__file__])