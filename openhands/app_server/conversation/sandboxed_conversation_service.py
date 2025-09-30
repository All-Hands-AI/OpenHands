import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable
from uuid import UUID

from openhands.app_server.conversation.conversation_models import (
    SandboxedConversation,
    SandboxedConversationPage,
    StartSandboxedConversationRequest,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class SandboxedConversationService(ABC):
    """Service for accessing conversations running in sandboxes to which the user has
    access
    """

    @abstractmethod
    async def search_sandboxed_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> SandboxedConversationPage:
        """Search for sandboxed conversations."""

    @abstractmethod
    async def count_sandboxed_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        """Count sandboxed conversations."""

    @abstractmethod
    async def get_sandboxed_conversation(
        self, conversation_id: UUID
    ) -> SandboxedConversation | None:
        """Get a single sandboxed conversation info. Return None if the conversation
        was not found.
        """

    async def batch_get_sandboxed_conversations(
        self, conversation_ids: list[UUID]
    ) -> list[SandboxedConversation | None]:
        """Get a batch of sandboxed conversations. Return None for any conversation
        which was not found.
        """
        return await asyncio.gather(
            *[
                self.get_sandboxed_conversation(conversation_id)
                for conversation_id in conversation_ids
            ]
        )

    @abstractmethod
    async def start_sandboxed_conversation(
        self, request: StartSandboxedConversationRequest
    ) -> SandboxedConversation:
        """Start a conversation, optionally specifying a sandbox in which to start. If
        no sandbox is specified a default may be used or started. This is a convenience
        method - the same effect should be achievable by creating / getting a sandbox
        id, starting a conversation, attaching a callback, and then running the
        conversation.
        """

    # Lifecycle methods

    async def __aenter__(self):
        """Start using this sandbox context"""
        return self

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Stop using this sandbox context"""


class SandboxedConversationServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_resolver_for_user(self) -> Callable:
        """Get a resolver which may be used to resolve an instance of sandbox spec service
        limited to the current user.
        """
