import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
    AppConversationInfoPage,
    AppConversationSortOrder,
)
from openhands.app_server.services.injector import Injector
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class AppConversationInfoService(ABC):
    """Service for accessing info on conversations without their current status."""

    @abstractmethod
    async def search_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        sort_order: AppConversationSortOrder = AppConversationSortOrder.CREATED_AT_DESC,
        page_id: str | None = None,
        limit: int = 100,
    ) -> AppConversationInfoPage:
        """Search for sandboxed conversations."""

    @abstractmethod
    async def count_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        """Count sandboxed conversations."""

    @abstractmethod
    async def get_app_conversation_info(
        self, conversation_id: UUID
    ) -> AppConversationInfo | None:
        """Get a single conversation info, returning None if missing."""

    async def batch_get_app_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversationInfo | None]:
        """Get a batch of conversation info, return None for any missing."""
        return await asyncio.gather(
            *[
                self.get_app_conversation_info(conversation_id)
                for conversation_id in conversation_ids
            ]
        )

    # Mutators

    @abstractmethod
    async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        """Store the sandboxed conversation info object given.

        Return the stored info
        """


class AppConversationInfoServiceInjector(
    DiscriminatedUnionMixin, Injector[AppConversationInfoService], ABC
):
    pass
