import asyncio
from abc import ABC, abstractmethod

from openhands.app_server.sandbox.sandbox_models import SandboxInfo, SandboxPage
from openhands.app_server.services.injector import Injector
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class SandboxService(ABC):
    """Service for accessing sandboxes in which conversations may be run."""

    @abstractmethod
    async def search_sandboxes(
        self,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxPage:
        """Search for sandboxes."""

    @abstractmethod
    async def get_sandbox(self, sandbox_id: str) -> SandboxInfo | None:
        """Get a single sandbox. Return None if the sandbox was not found."""

    async def batch_get_sandboxes(
        self, sandbox_ids: list[str]
    ) -> list[SandboxInfo | None]:
        """Get a batch of sandboxes, returning None for any which were not found."""
        results = await asyncio.gather(
            *[self.get_sandbox(sandbox_id) for sandbox_id in sandbox_ids]
        )
        return results

    @abstractmethod
    async def start_sandbox(self, sandbox_spec_id: str | None = None) -> SandboxInfo:
        """Begin the process of starting a sandbox.

        Return the info on the new sandbox. If no spec is selected, use the default.
        """

    @abstractmethod
    async def resume_sandbox(self, sandbox_id: str) -> bool:
        """Begin the process of resuming a sandbox.

        Return True if the sandbox exists and is being resumed or is already running.
        Return False if the sandbox did not exist.
        """

    @abstractmethod
    async def pause_sandbox(self, sandbox_id: str) -> bool:
        """Begin the process of pausing a sandbox.

        Return True if the sandbox exists and is being paused or is already paused.
        Return False if the sandbox did not exist.
        """

    @abstractmethod
    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Begin the process of deleting a sandbox (which may involve stopping it).

        Return False if the sandbox did not exist.
        """


class SandboxServiceInjector(DiscriminatedUnionMixin, Injector[SandboxService], ABC):
    pass
