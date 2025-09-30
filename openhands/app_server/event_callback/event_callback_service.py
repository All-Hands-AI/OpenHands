import asyncio
from abc import ABC, abstractmethod
from typing import Callable
from uuid import UUID

from openhands.app_server.event_callback.event_callback_models import (
    CreateEventCallbackRequest,
    EventCallback,
    EventCallbackPage,
    EventKind,
)
from openhands.sdk import EventBase
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class EventCallbackService(ABC):
    """CRUD service for managing event callbacks."""

    @abstractmethod
    async def create_event_callback(
        self, request: CreateEventCallbackRequest
    ) -> EventCallback:
        """Create a new event callback."""

    @abstractmethod
    async def get_event_callback(self, id: UUID) -> EventCallback | None:
        """Get a single event callback, returning None if not found."""

    @abstractmethod
    async def delete_event_callback(self, id: UUID) -> bool:
        """Delete a event callback, returning True if deleted, False if not found."""

    @abstractmethod
    async def search_event_callbacks(
        self,
        conversation_id__eq: UUID | None = None,
        event_kind__eq: EventKind | None = None,
        event_id__eq: UUID | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> EventCallbackPage:
        """Search for event callbacks, optionally filtered by event_id."""

    async def batch_get_event_callbacks(
        self, event_callback_ids: list[UUID]
    ) -> list[EventCallback | None]:
        """Get a batch of event callbacks, returning None for any not found."""
        results = await asyncio.gather(
            *[
                self.get_event_callback(event_callback_id)
                for event_callback_id in event_callback_ids
            ]
        )
        return results

    @abstractmethod
    async def execute_callbacks(self, conversation_id: UUID, event: EventBase) -> None:
        """Execute any applicable callbacks for the event and store the results."""

    # Lifecycle methods

    async def __aenter__(self):
        """Start using this event callback service."""
        return self

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Stop using this event callback service."""


class EventCallbackServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_unsecured_resolver(self) -> Callable:
        """Get a resolver for an instance of event callback service."""

    @abstractmethod
    def get_resolver_for_user(self) -> Callable:
        """Get a resolver for an instance of event callback service limited to the current user."""
