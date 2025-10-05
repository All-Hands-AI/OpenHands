import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import Callable

from pydantic import Field

from openhands.app_server.errors import OpenHandsError, SandboxError
from openhands.app_server.sandbox.sandbox_spec_models import (
    SandboxSpecInfo,
    SandboxSpecInfoPage,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin

from openhands.app_server.sandbox.sandbox_spec_service import SandboxSpecService, SandboxSpecServiceManager


@dataclass
class RemoteSandboxSpecService(SandboxSpecService):
    """Service for managing Sandbox specs in the Remote Runtime API.

    At present, the runtime API exposes methods to check whether a paricular image
    exists, but not to list existing images - so we maintain a list of images locally
    and check on startup that these exist within the runtime API.
    """
    specs: list[SandboxSpecInfo]

    async def search_sandbox_specs(
        self, page_id: str | None = None, limit: int = 100
    ) -> SandboxSpecInfoPage:
        raise NotImplementedError()

    async def get_sandbox_spec(self, sandbox_spec_id: str) -> SandboxSpecInfo | None:
        raise NotImplementedError()

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
            working_dir='/home/openhands'
        )
    ]


class RemoteSandboxSpecServiceManager(SandboxSpecServiceManager):
    specs: list[SandboxSpecInfo] = Field(
        default_factory=_get_specs_from_legacy_parameter,
        description="Preset list of sandbox specs. Falls back to legacy parameter",
    )

    def get_resolver_for_current_user(self) -> Callable:
        # At present, all specs are available to all users within the system
        return self.get_unsecured_resolver()

    def get_unsecured_resolver(self) -> Callable:
        return self._resolve

    def _resolve(self):
        return RemoteSandboxSpecService(self.specs)
