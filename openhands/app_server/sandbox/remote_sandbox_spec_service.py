import logging
from dataclasses import dataclass
from typing import AsyncGenerator, cast

from fastapi import Request
from pydantic import Field

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


class RemoteSandboxSpecInfo(SandboxSpecInfo):
    command: list[str] | None = Field(
        default_factory=lambda: ['/usr/local/bin/agent-server', '--port', '60000']
    )
    initial_env: dict[str, str] = Field(
        default_factory=lambda: {
            'OPENVSCODE_SERVER_ROOT': '/openhands/.openvscode-server',
            'LOG_JSON': 'true',
        }
    )
    working_dir: str = Field(default='/workspace')


class RemoteSandboxSpecServiceInjector(SandboxSpecServiceInjector):
    specs: list[RemoteSandboxSpecInfo] = Field(
        default_factory=list,
        description='Preset list of sandbox specs',
    )

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[SandboxSpecService, None]:
        yield RemoteSandboxSpecService(cast(list[SandboxSpecInfo], self.specs))
