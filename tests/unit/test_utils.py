"""
Test utilities for handling environment dependencies in tests.

This module provides utilities to make tests independent of external environment
peculiarities such as authentication tokens, Docker availability, etc.
"""

import os
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def disable_session_api_key():
    """
    Context manager to disable SESSION_API_KEY authentication in tests.

    This ensures tests are not dependent on the external environment's
    SESSION_API_KEY setting.
    """
    with (
        patch.dict(os.environ, {'SESSION_API_KEY': ''}, clear=False),
        patch('openhands.server.dependencies._SESSION_API_KEY', None),
    ):
        yield


@contextmanager
def mock_docker_unavailable():
    """
    Context manager to mock Docker as unavailable for tests that don't need it.

    This prevents tests from failing when Docker is not available in the
    testing environment.
    """
    from docker.errors import DockerException

    def mock_docker_from_env(*args, **kwargs):
        raise DockerException('Docker not available in test environment')

    with patch('docker.from_env', side_effect=mock_docker_from_env):
        yield


@contextmanager
def mock_docker_client():
    """
    Context manager to provide a mock Docker client for tests.

    This provides a functional mock Docker client that can be used in tests
    without requiring an actual Docker daemon.
    """
    from unittest.mock import MagicMock

    import docker

    mock_client = MagicMock(spec=docker.DockerClient)
    mock_client.version.return_value = {
        'Version': '20.10.0',
        'Components': [{'Name': 'Engine', 'Version': '20.10.0'}],
    }

    # Mock images
    mock_images = MagicMock()
    mock_images.build.return_value = (MagicMock(), [])
    mock_images.get.return_value = MagicMock()
    mock_images.list.return_value = []
    mock_client.images = mock_images

    # Mock containers
    mock_containers = MagicMock()
    mock_containers.run.return_value = MagicMock()
    mock_containers.list.return_value = []
    mock_client.containers = mock_containers

    with patch('docker.from_env', return_value=mock_client):
        yield mock_client


@contextmanager
def mock_llm_api_key():
    """
    Context manager to provide a mock LLM API key for tests.

    This prevents tests from failing due to missing or invalid API keys.
    """
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}, clear=False):
        yield
