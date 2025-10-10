import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

import docker
from docker.errors import APIError, NotFound
from fastapi import Request
from pydantic import Field

from openhands.agent_server.utils import utc_now
from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.sandbox_spec_models import (
    SandboxSpecInfo,
    SandboxSpecInfoPage,
)
from openhands.app_server.sandbox.sandbox_spec_service import (
    SandboxSpecService,
    SandboxSpecServiceInjector,
)
from openhands.app_server.services.injector import InjectorState

_global_docker_client: docker.DockerClient | None = None
_logger = logging.getLogger(__name__)


def get_docker_client() -> docker.DockerClient:
    global _global_docker_client
    if _global_docker_client is None:
        _global_docker_client = docker.from_env()
    return _global_docker_client


@dataclass
class DockerSandboxSpecService(SandboxSpecService):
    """Sandbox spec service for docker images.

    By default, all images with the repository given are loaded and returned, though
    they may have different tags. The combination of the repository and tag is treated
    as the id in the resulting image.
    """

    repository: str
    command: list[str] | None
    initial_env: dict[str, str]
    working_dir: str
    pull_if_missing: bool
    created_at__gte: datetime | None
    docker_client: docker.DockerClient = field(default_factory=get_docker_client)

    def _docker_image_to_sandbox_specs(self, image) -> SandboxSpecInfo:
        """Convert a Docker image to SandboxSpecInfo."""
        # Extract repository and tag from image tags
        # Use the first tag if multiple tags exist, or use the image ID if no tags
        if image.tags:
            image_id = image.tags[0]  # Use repository:tag as ID
        else:
            image_id = image.id[:12]  # Use short image ID if no tags

        # Parse creation time from image attributes
        created_str = image.attrs.get('Created', '')
        try:
            # Docker timestamps are in ISO format
            created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
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
        """Search for runtime images."""
        try:
            # Get all images that match the repository
            images = self.docker_client.images.list(name=self.repository)

            # Convert Docker images to SandboxSpecInfo
            sandbox_specs: list[SandboxSpecInfo] = []
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

            # Filter old images
            if self.created_at__gte:
                sandbox_specs = [
                    sandbox_spec
                    for sandbox_spec in sandbox_specs
                    if sandbox_spec.created_at >= self.created_at__gte
                ]

            # Sort by created_at descending
            sandbox_specs.sort(key=lambda s: s.created_at, reverse=True)

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
        """Get a single runtime image info by ID."""
        try:
            # Try to get the image by ID (which should be repository:tag)
            image = self.docker_client.images.get(sandbox_spec_id)
            sandbox_spec = self._docker_image_to_sandbox_specs(image)
            if (
                self.created_at__gte is None
                or sandbox_spec.created_at >= self.created_at__gte
            ):
                return sandbox_spec
            return None
        except (NotFound, APIError):
            return None

    async def get_default_sandbox_spec(self):
        # If there are specs, pick the most recent one...
        page = await self.search_sandbox_specs()
        if page.items:
            return page.items[0]

        if self.pull_if_missing:
            try:
                _logger.info(f'⬇️ Pulling Docker Image {self.repository}')
                # Pull in a background thread to prevent locking up the main runloop
                # This actually fails at the moment because the latest images are
                # not being tagged
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, self.docker_client.images.pull, self.repository
                )
                page = await self.search_sandbox_specs()
                return page.items[0]
            except Exception as exc:
                raise SandboxError('Error pulling docker image!') from exc
        else:
            raise SandboxError(
                'No sandbox specs available! '
                f'(Maybe you need to `docker pull {self.repository}:latest`)'
            )


class DockerSandboxSpecServiceInjector(SandboxSpecServiceInjector):
    repository: str = 'ghcr.io/all-hands-ai/agent-server'
    command: list[str] | None = None
    initial_env: dict[str, str] = Field(
        default_factory=lambda: {
            'OPENVSCODE_SERVER_ROOT': '/openhands/.openvscode-server',
            'LOG_JSON': 'true',
        }
    )
    working_dir: str = '/home/openhands'
    pull_if_missing: bool = Field(
        default=True,
        description=(
            'Flag indicating that if docker does not have a suitable image '
            'one should be pulled.'
        ),
    )
    created_at__gte: datetime | None = Field(
        default=datetime.fromisoformat('2025-10-10T00:00:00+00:00'),
        description='The min age for a suitable image',
    )

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[SandboxSpecService, None]:
        yield DockerSandboxSpecService(
            repository=self.repository,
            command=self.command,
            initial_env=self.initial_env,
            working_dir=self.working_dir,
            pull_if_missing=self.pull_if_missing,
            created_at__gte=self.created_at__gte,
        )
