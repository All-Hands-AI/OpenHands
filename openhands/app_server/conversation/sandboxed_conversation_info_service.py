import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable
from uuid import UUID

from openhands.app_server.conversation.conversation_models import (
    SandboxedConversationInfo,
    SandboxedConversationInfoPage,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class SandboxedConversationInfoService(ABC):
    """Service for accessing info on conversations without their current status"""

    @abstractmethod
    async def search_sandboxed_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxedConversationInfoPage:
        """Search for sandboxed conversations."""

    @abstractmethod
    async def count_sandboxed_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        """Count sandboxed conversations."""

    @abstractmethod
    async def get_sandboxed_conversation_info(
        self, conversation_id: UUID
    ) -> SandboxedConversationInfo | None:
        """Get a single conversation info. Return None if the conversation
        was not found.
        """

    async def batch_get_sandboxed_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[SandboxedConversationInfo | None]:
        """Get a batch of conversation info. Return None for any conversation
        which was not found.
        """
        return await asyncio.gather(
            *[
                self.get_sandboxed_conversation_info(conversation_id)
                for conversation_id in conversation_ids
            ]
        )

    # Mutators

    @abstractmethod
    async def save_sandboxed_conversation_info(
        self, info: SandboxedConversationInfo
    ) -> bool:
        """Store the sandboxed conversation info object given.
        Return true if it was stored, false otherwise
        """

    # Lifecycle methods

    async def __aenter__(self):
        """Start using this sandbox context"""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Stop using this sandbox context"""


class SandboxedConversationInfoServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_resolver_for_user(self) -> Callable:
        """Get a resolver which may be used to resolve an instance of sandbox spec service
        limited to the current user.
        """
