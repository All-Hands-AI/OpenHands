import asyncio
from abc import ABC, abstractmethod
from typing import Callable
from uuid import UUID

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationStartTask,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class AppConversationStartTaskService(ABC):
    """Service for accessing start tasks for conversations."""

    # TODO: We can add the standard search, count, and batch methods later

    @abstractmethod
    async def get_app_conversation_start_task(
        self, task_id: UUID
    ) -> AppConversationStartTask | None:
        """Get a single start task, returning None if missing."""

    async def batch_get_app_conversation_start_tasks(
        self, task_ids: list[UUID]
    ) -> list[AppConversationStartTask | None]:
        """Get a batch of start tasks, return None for any missing."""
        return await asyncio.gather(
            *[self.get_app_conversation_start_task(task_id) for task_id in task_ids]
        )

    # Mutators

    @abstractmethod
    async def save_app_conversation_start_task(
        self, info: AppConversationStartTask
    ) -> bool:
        """Store the start task object given.

        Return true if it was stored, false otherwise.
        """


class AppConversationStartTaskServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_unsecured_resolver(self) -> Callable:
        """Get a resolver for an instance of app conversation start task service."""

    @abstractmethod
    def get_resolver_for_user(self) -> Callable:
        """Get a resolver for an instance of app conversation start task service limited to the current user."""
