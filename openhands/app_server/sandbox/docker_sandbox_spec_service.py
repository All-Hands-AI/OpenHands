import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import docker
from docker.errors import APIError, NotFound

from openhands.app_server.sandbox.sandbox_spec_models import (
    SandboxSpecInfo,
    SandboxSpecInfoPage,
)
from openhands.app_server.sandbox.sandbox_spec_service import (
    SandboxSpecService,
    SandboxSpecServiceResolver,
)
from openhands.app_server.utils.date_utils import utc_now


_global_docker_client: docker.DockerClient | None = None
_logger = logging.getLogger(__name__)


def get_docker_client() -> docker.DockerClient:
    global _global_docker_client
    if _global_docker_client is None:
        _global_docker_client = docker.from_env()
    return _global_docker_client


@dataclass
class DockerSandboxSpecService(SandboxSpecService):
    """Sandbox spec service for docker images. By default, all images with the
    repository given are loaded and returned (They may have different tag) The
    combination of the repository and tag is treated as the id in the resulting image.
    """

    docker_client: docker.DockerClient = field(default_factory=get_docker_client)
    repository: str = "ghcr.io/all-hands-ai/agent-server"
    command: str = "/usr/local/bin/openhands-agent-server"
    initial_env: dict[str, str] = field(
        default_factory=lambda: {
            "OPENVSCODE_SERVER_ROOT": "/openhands/.openvscode-server",
            "LOG_JSON": "true",
        }
    )
    working_dir: str = "/home/openhands"

    def _docker_image_to_sandbox_specs(self, image) -> SandboxSpecInfo:
        """Convert a Docker image to SandboxSpecInfo"""
        # Extract repository and tag from image tags
        # Use the first tag if multiple tags exist, or use the image ID if no tags
        if image.tags:
            image_id = image.tags[0]  # Use repository:tag as ID
        else:
            image_id = image.id[:12]  # Use short image ID if no tags

        # Parse creation time from image attributes
        created_str = image.attrs.get("Created", "")
        try:
            # Docker timestamps are in ISO format
            created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = utc_now()

        return SandboxSpecInfo(
            id=image_id,
            command=self.command,
            created_at=created_at,
            initial_env=self.initial_env,
            working_dir=self.working_dir,
        )

    async def search_sandbox_specs(
        self, page_id: str | None = None, limit: int = 100
    ) -> SandboxSpecInfoPage:
        """Search for runtime images"""
        try:
            # Get all images that match the repository
            images = self.docker_client.images.list(name=self.repository)

            # Convert Docker images to SandboxSpecInfo
            sandbox_specs = []
            for image in images:
                # Only include images that have tags matching our repository
                if image.tags:
                    for tag in image.tags:
                        if tag.startswith(self.repository):
                            sandbox_specs.append(
                                self._docker_image_to_sandbox_specs(image)
                            )
                            # Only add once per image, even if multiple matching tags
                            break

            # Apply pagination
            start_idx = 0
            if page_id:
                try:
                    start_idx = int(page_id)
                except ValueError:
                    start_idx = 0

            end_idx = start_idx + limit
            paginated_images = sandbox_specs[start_idx:end_idx]

            # Determine next page ID
            next_page_id = None
            if end_idx < len(sandbox_specs):
                next_page_id = str(end_idx)

            return SandboxSpecInfoPage(
                items=paginated_images, next_page_id=next_page_id
            )

        except APIError:
            # Return empty page if there's an API error
            return SandboxSpecInfoPage(items=[], next_page_id=None)

    async def get_sandbox_spec(self, sandbox_spec_id: str) -> SandboxSpecInfo | None:
        """Get a single runtime image info by ID"""
        try:
            # Try to get the image by ID (which should be repository:tag)
            image = self.docker_client.images.get(sandbox_spec_id)
            return self._docker_image_to_sandbox_specs(image)
        except (NotFound, APIError):
            return None


class DockerSandboxSpecServiceResolver(SandboxSpecServiceResolver):
    def get_resolver_for_user(self) -> Callable:
        # Docker sandboxes are designed for a single user and
        # don't have security constraints
        return self.resolve

    def resolve(self) -> SandboxSpecService:
        return DockerSandboxSpecService()
