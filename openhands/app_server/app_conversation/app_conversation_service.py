import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable
from uuid import UUID

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversation,
    AppConversationPage,
    StartAppConversationRequest,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class AppConversationService(ABC):
    """Service for managing conversations running in sandboxes."""

    @abstractmethod
    async def search_app_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> AppConversationPage:
        """Search for sandboxed conversations."""

    @abstractmethod
    async def count_app_conversations(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        """Count sandboxed conversations."""

    @abstractmethod
    async def get_app_conversation(
        self, conversation_id: UUID
    ) -> AppConversation | None:
        """Get a single sandboxed conversation info. Return None if missing."""

    async def batch_get_app_conversations(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversation | None]:
        """Get a batch of sandboxed conversations, returning None for any missing."""
        return await asyncio.gather(
            *[
                self.get_app_conversation(conversation_id)
                for conversation_id in conversation_ids
            ]
        )

    @abstractmethod
    async def start_app_conversation(
        self, request: StartAppConversationRequest
    ) -> AppConversation:
        """Start a conversation, optionally specifying a sandbox in which to start.

        If no sandbox is specified a default may be used or started. This is a convenience
        method - the same effect should be achievable by creating / getting a sandbox
        id, starting a conversation, attaching a callback, and then running the
        conversation.
        """

    # Lifecycle methods

    async def __aenter__(self):
        """Start using this sandbox context."""
        return self

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Stop using this sandbox context."""


class AppConversationServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_resolver_for_user(self) -> Callable:
        """Get a resolver for an instance of sandbox spec service limited to the current user."""
