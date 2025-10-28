import asyncio
import logging
from typing import AsyncGenerator

import docker
from fastapi import Request
from pydantic import Field

from openhands.app_server.errors import SandboxError
from openhands.app_server.sandbox.preset_sandbox_spec_service import (
    PresetSandboxSpecService,
)
from openhands.app_server.sandbox.sandbox_spec_models import (
    SandboxSpecInfo,
)
from openhands.app_server.sandbox.sandbox_spec_service import (
    AGENT_SERVER_IMAGE,
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


def get_default_sandbox_specs():
    return [
        SandboxSpecInfo(
            id=AGENT_SERVER_IMAGE,
            command=['--port', '8000'],
            initial_env={
                'OPENVSCODE_SERVER_ROOT': '/openhands/.openvscode-server',
                'OH_ENABLE_VNC': '0',
                'LOG_JSON': 'true',
                'OH_CONVERSATIONS_PATH': '/home/openhands/conversations',
                'OH_BASH_EVENTS_DIR': '/home/openhands/bash_events',
            },
            working_dir='/home/openhands/workspace',
        )
    ]


class DockerSandboxSpecServiceInjector(SandboxSpecServiceInjector):
    specs: list[SandboxSpecInfo] = Field(
        default_factory=get_default_sandbox_specs,
        description='Preset list of sandbox specs',
    )
    pull_if_missing: bool = Field(
        default=True,
        description=(
            'Flag indicating that any missing specs should be pulled from '
            'remote repositories.'
        ),
    )

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[SandboxSpecService, None]:
        if self.pull_if_missing:
            await self.pull_missing_specs()
            # Prevent repeated checks - more efficient but it does mean if you
            # delete a docker image outside the app you need to restart
            self.pull_if_missing = False
        yield PresetSandboxSpecService(specs=self.specs)

    async def pull_missing_specs(self):
        await asyncio.gather(*[self.pull_spec_if_missing(spec) for spec in self.specs])

    async def pull_spec_if_missing(self, spec: SandboxSpecInfo):
        _logger.debug(f'Checking Docker Image: {spec.id}')
        try:
            docker_client = get_docker_client()
            try:
                docker_client.images.get(spec.id)
            except docker.errors.ImageNotFound:
                _logger.info(f'⬇️ Pulling Docker Image: {spec.id}')
                # Pull in a background thread to prevent locking up the main runloop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, docker_client.images.pull, spec.id)
                _logger.info(f'⬇️ Finished Pulling Docker Image: {spec.id}')
        except docker.errors.APIError as exc:
            raise SandboxError(f'Error Getting Docker Image: {spec.id}') from exc
