import asyncio
import logging
import os
from dataclasses import dataclass
from typing import AsyncGenerator

from fastapi import Request
import httpx
from pydantic import Field, PrivateAttr

from openhands.app_server.errors import OpenHandsError
from openhands.app_server.sandbox.sandbox_spec_models import (
    SandboxSpecInfo,
    SandboxSpecInfoPage,
)
from openhands.app_server.sandbox.sandbox_spec_service import (
    SandboxSpecService,
    SandboxSpecServiceInjector,
)
from openhands.app_server.services.injector import InjectorState

_logger = logging.getLogger(__name__)


@dataclass
class RemoteSandboxSpecService(SandboxSpecService):
    """Service for managing Sandbox specs in the Remote Runtime API.

    At present, the runtime API exposes methods to check whether a paricular image
    exists, but not to list existing images - so we maintain a list of images locally.
    """

    specs: list[SandboxSpecInfo]

    async def search_sandbox_specs(
        self, page_id: str | None = None, limit: int = 100
    ) -> SandboxSpecInfoPage:
        """Search for sandbox specs with pagination support."""
        # Apply pagination
        start_idx = 0
        if page_id:
            try:
                start_idx = int(page_id)
            except ValueError:
                start_idx = 0

        end_idx = start_idx + limit
        paginated_specs = self.specs[start_idx:end_idx]

        # Determine next page ID
        next_page_id = None
        if end_idx < len(self.specs):
            next_page_id = str(end_idx)

        return SandboxSpecInfoPage(items=paginated_specs, next_page_id=next_page_id)

    async def get_sandbox_spec(self, sandbox_spec_id: str) -> SandboxSpecInfo | None:
        """Get a single sandbox spec by ID, returning None if not found."""
        for spec in self.specs:
            if spec.id == sandbox_spec_id:
                return spec
        return None

    async def get_default_sandbox_spec(self) -> SandboxSpecInfo:
        return self.specs[0]


def _get_specs_from_legacy_parameter():
    """If no config for SnadboxSpecs is defined, build one using the legacy param."""
    image = os.getenv('SANDBOX_RUNTIME_CONTAINER_IMAGE')
    if not image:
        raise OpenHandsError('Please set sandbox specs!')
    return [
        SandboxSpecInfo(
            id=image,
            command='/usr/local/bin/openhands-agent-server',
            initial_env={
                'OPENVSCODE_SERVER_ROOT': '/openhands/.openvscode-server',
                'LOG_JSON': 'true',
            },
            working_dir='/home/openhands',
        )
    ]


class RemoteSandboxSpecServiceInjector(SandboxSpecServiceInjector):
    specs: list[SandboxSpecInfo] = Field(
        default_factory=_get_specs_from_legacy_parameter,
        description='Preset list of sandbox specs. Falls back to legacy parameter',
    )

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[SandboxSpecService, None]:
        yield RemoteSandboxSpecService(self.specs)
