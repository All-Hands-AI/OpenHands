"""Tests for DockerSandboxSpecService.

This module tests the Docker sandbox spec service implementation, focusing on:
- Docker image listing and retrieval
- Image data transformation to SandboxSpecInfo objects
- Pagination and filtering logic
- Error handling for Docker API failures
- Edge cases with malformed or missing image data
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from docker.errors import APIError, NotFound

from openhands.app_server.sandbox.docker_sandbox_spec_service import (
    DockerSandboxSpecService,
    get_docker_client,
)
from openhands.app_server.sandbox.sandbox_spec_models import (
    SandboxSpecInfo,
    SandboxSpecInfoPage,
)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing."""
    with patch(
        "openhands.app_server.sandbox.docker_sandbox_spec_service.get_docker_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_image():
    """Create a mock Docker image object."""
    image = MagicMock()
    image.tags = ["ghcr.io/all-hands-ai/agent-server:latest"]
    image.id = "sha256:abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
    image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}
    return image


@pytest.fixture
def mock_image_no_tags():
    """Create a mock Docker image object without tags."""
    image = MagicMock()
    image.tags = []
    image.id = "sha256:abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
    image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}
    return image


@pytest.fixture
def mock_image_multiple_tags():
    """Create a mock Docker image object with multiple tags."""
    image = MagicMock()
    image.tags = [
        "ghcr.io/all-hands-ai/agent-server:latest",
        "ghcr.io/all-hands-ai/agent-server:v1.0.0",
        "other-repo/image:tag",
    ]
    image.id = "sha256:abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
    image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}
    return image


@pytest.fixture
def service(mock_docker_client):
    """Create DockerSandboxSpecService instance for testing."""
    return DockerSandboxSpecService(docker_client=mock_docker_client.return_value)


class TestDockerSandboxSpecService:
    """Test cases for DockerSandboxSpecService."""

    async def test_search_sandbox_specs_success(
        self, service, mock_docker_client, mock_image
    ):
        """Test successful search for sandbox specs."""
        # Setup
        service.docker_client.images.list.return_value = [mock_image]

        # Execute
        result = await service.search_sandbox_specs()

        # Verify
        assert isinstance(result, SandboxSpecInfoPage)
        assert len(result.items) == 1
        assert result.next_page_id is None

        spec_info = result.items[0]
        assert spec_info.id == "ghcr.io/all-hands-ai/agent-server:latest"
        assert spec_info.command == "/usr/local/bin/openhands-agent-server"
        assert spec_info.working_dir == "/home/openhands"
        assert "OPENVSCODE_SERVER_ROOT" in spec_info.initial_env

        # Verify Docker client was called correctly
        service.docker_client.images.list.assert_called_once_with(
            name="ghcr.io/all-hands-ai/agent-server"
        )

    async def test_search_sandbox_specs_multiple_images(
        self, service, mock_docker_client, mock_image, mock_image_multiple_tags
    ):
        """Test search with multiple images."""
        # Setup
        service.docker_client.images.list.return_value = [
            mock_image,
            mock_image_multiple_tags,
        ]

        # Execute
        result = await service.search_sandbox_specs()

        # Verify
        assert len(result.items) == 2
        assert result.items[0].id == "ghcr.io/all-hands-ai/agent-server:latest"
        assert (
            result.items[1].id == "ghcr.io/all-hands-ai/agent-server:latest"
        )  # First matching tag

    async def test_search_sandbox_specs_no_matching_tags(
        self, service, mock_docker_client
    ):
        """Test search with images that don't match repository."""
        # Setup
        non_matching_image = MagicMock()
        non_matching_image.tags = ["other-repo/image:tag"]
        non_matching_image.id = "sha256:1234567890abcdef"
        non_matching_image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}

        service.docker_client.images.list.return_value = [non_matching_image]

        # Execute
        result = await service.search_sandbox_specs()

        # Verify
        assert len(result.items) == 0
        assert result.next_page_id is None

    async def test_search_sandbox_specs_pagination(self, service, mock_docker_client):
        """Test pagination functionality."""
        # Setup - create multiple mock images
        images = []
        for i in range(5):
            image = MagicMock()
            image.tags = [f"ghcr.io/all-hands-ai/agent-server:v{i}"]
            image.id = f"sha256:abcd{i:04d}"
            image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}
            images.append(image)

        service.docker_client.images.list.return_value = images

        # Execute - first page
        result = await service.search_sandbox_specs(limit=3)

        # Verify first page
        assert len(result.items) == 3
        assert result.next_page_id == "3"

        # Execute - second page
        result = await service.search_sandbox_specs(page_id="3", limit=3)

        # Verify second page
        assert len(result.items) == 2
        assert result.next_page_id is None

    async def test_search_sandbox_specs_invalid_page_id(
        self, service, mock_docker_client, mock_image
    ):
        """Test handling of invalid page ID."""
        # Setup
        service.docker_client.images.list.return_value = [mock_image]

        # Execute
        result = await service.search_sandbox_specs(page_id="invalid")

        # Verify - should start from beginning
        assert len(result.items) == 1

    async def test_search_sandbox_specs_docker_api_error(
        self, service, mock_docker_client
    ):
        """Test handling of Docker API errors."""
        # Setup
        service.docker_client.images.list.side_effect = APIError("Docker daemon error")

        # Execute
        result = await service.search_sandbox_specs()

        # Verify
        assert isinstance(result, SandboxSpecInfoPage)
        assert len(result.items) == 0
        assert result.next_page_id is None

    async def test_get_sandbox_spec_success(
        self, service, mock_docker_client, mock_image
    ):
        """Test successful retrieval of specific sandbox spec."""
        # Setup
        service.docker_client.images.get.return_value = mock_image

        # Execute
        result = await service.get_sandbox_spec(
            "ghcr.io/all-hands-ai/agent-server:latest"
        )

        # Verify
        assert result is not None
        assert result.id == "ghcr.io/all-hands-ai/agent-server:latest"
        assert result.command == "/usr/local/bin/openhands-agent-server"

        # Verify Docker client was called correctly
        service.docker_client.images.get.assert_called_once_with(
            "ghcr.io/all-hands-ai/agent-server:latest"
        )

    async def test_get_sandbox_spec_not_found(self, service, mock_docker_client):
        """Test handling when sandbox spec is not found."""
        # Setup
        service.docker_client.images.get.side_effect = NotFound("Image not found")

        # Execute
        result = await service.get_sandbox_spec("nonexistent:tag")

        # Verify
        assert result is None

    async def test_get_sandbox_spec_api_error(self, service, mock_docker_client):
        """Test handling of Docker API errors during get."""
        # Setup
        service.docker_client.images.get.side_effect = APIError("Docker daemon error")

        # Execute
        result = await service.get_sandbox_spec(
            "ghcr.io/all-hands-ai/agent-server:latest"
        )

        # Verify
        assert result is None

    def test_docker_image_to_sandbox_specs_with_tags(self, service, mock_image):
        """Test conversion of Docker image to SandboxSpecInfo with tags."""
        # Execute
        result = service._docker_image_to_sandbox_specs(mock_image)

        # Verify
        assert isinstance(result, SandboxSpecInfo)
        assert result.id == "ghcr.io/all-hands-ai/agent-server:latest"
        assert result.command == "/usr/local/bin/openhands-agent-server"
        assert result.working_dir == "/home/openhands"
        assert (
            result.initial_env["OPENVSCODE_SERVER_ROOT"]
            == "/openhands/.openvscode-server"
        )
        assert result.initial_env["LOG_JSON"] == "true"
        assert isinstance(result.created_at, datetime)

    def test_docker_image_to_sandbox_specs_no_tags(self, service, mock_image_no_tags):
        """Test conversion of Docker image without tags."""
        # Execute
        result = service._docker_image_to_sandbox_specs(mock_image_no_tags)

        # Verify
        assert isinstance(result, SandboxSpecInfo)
        assert result.id == "sha256:abcd1"  # First 12 characters of image ID
        assert result.command == "/usr/local/bin/openhands-agent-server"

    def test_docker_image_to_sandbox_specs_invalid_created_time(self, service):
        """Test handling of invalid creation timestamp."""
        # Setup
        image = MagicMock()
        image.tags = ["ghcr.io/all-hands-ai/agent-server:latest"]
        image.id = (
            "sha256:abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
        )
        image.attrs = {"Created": "invalid-timestamp"}

        # Execute
        result = service._docker_image_to_sandbox_specs(image)

        # Verify - should use current time as fallback
        assert isinstance(result, SandboxSpecInfo)
        assert isinstance(result.created_at, datetime)

    def test_docker_image_to_sandbox_specs_missing_created_time(self, service):
        """Test handling of missing creation timestamp."""
        # Setup
        image = MagicMock()
        image.tags = ["ghcr.io/all-hands-ai/agent-server:latest"]
        image.id = (
            "sha256:abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
        )
        image.attrs = {}

        # Execute
        result = service._docker_image_to_sandbox_specs(image)

        # Verify - should use current time as fallback
        assert isinstance(result, SandboxSpecInfo)
        assert isinstance(result.created_at, datetime)

    async def test_search_sandbox_specs_filters_by_repository(
        self, service, mock_docker_client
    ):
        """Test that search properly filters images by repository."""
        # Setup
        matching_image = MagicMock()
        matching_image.tags = ["ghcr.io/all-hands-ai/agent-server:latest"]
        matching_image.id = "sha256:abcd1234"
        matching_image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}

        non_matching_image = MagicMock()
        non_matching_image.tags = ["other-repo/image:tag"]
        non_matching_image.id = "sha256:efgh5678"
        non_matching_image.attrs = {"Created": "2024-01-15T10:30:00.000000000Z"}

        service.docker_client.images.list.return_value = [
            matching_image,
            non_matching_image,
        ]

        # Execute
        result = await service.search_sandbox_specs()

        # Verify - only matching image should be included
        assert len(result.items) == 1
        assert result.items[0].id == "ghcr.io/all-hands-ai/agent-server:latest"

    async def test_search_sandbox_specs_multiple_matching_tags_single_entry(
        self, service, mock_docker_client, mock_image_multiple_tags
    ):
        """Test that image with multiple matching tags only appears once."""
        # Setup
        service.docker_client.images.list.return_value = [mock_image_multiple_tags]

        # Execute
        result = await service.search_sandbox_specs()

        # Verify - should only appear once despite multiple matching tags
        assert len(result.items) == 1
        assert (
            result.items[0].id == "ghcr.io/all-hands-ai/agent-server:latest"
        )  # First matching tag


class TestGetDockerClient:
    """Test cases for get_docker_client function."""

    @patch("docker.from_env")
    def test_get_docker_client_creates_new_client(self, mock_from_env):
        """Test that get_docker_client creates a new client when none exists."""
        # Setup
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        # Reset global client
        import openhands.app_server.sandbox.docker_sandbox_spec_service as module

        module._global_docker_client = None

        # Execute
        result = get_docker_client()

        # Verify
        assert result == mock_client
        mock_from_env.assert_called_once()

    @patch("docker.from_env")
    def test_get_docker_client_reuses_existing_client(self, mock_from_env):
        """Test that get_docker_client reuses existing client."""
        # Setup
        mock_client = MagicMock()
        import openhands.app_server.sandbox.docker_sandbox_spec_service as module

        module._global_docker_client = mock_client

        # Execute
        result = get_docker_client()

        # Verify
        assert result == mock_client
        mock_from_env.assert_not_called()
