from uuid import UUID

from openhands.app_server.event_callback.event_callback_models import (
    CreateEventCallbackRequest,
    EventCallback,
    EventCallbackPage,
    EventKind,
)
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackService,
)
from openhands.sdk import EventBase


class NoopEventCallbackService(EventCallbackService):
    """Currently OSS does not have the concept of event callbacks, so a Noop is required. (In
    future if we migrate users and permissions we can flesh this out)
    """

    async def create_event_callback(
        self, request: CreateEventCallbackRequest
    ) -> EventCallback:
        """Create a new event callback"""
        raise NotImplementedError('Event callbacks are not supported in OSS')

    async def get_event_callback(self, id: UUID) -> EventCallback | None:
        """Get a single event callback, returning None if not found."""
        return None

    async def delete_event_callback(self, id: UUID) -> bool:
        """Delete a event callback, returning True if deleted, False if not found."""
        return False

    async def search_event_callbacks(
        self,
        conversation_id__eq: UUID | None = None,
        event_kind__eq: EventKind | None = None,
        event_id__eq: UUID | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> EventCallbackPage:
        return EventCallbackPage(items=[])

    async def execute_callbacks(self, conversation_id: UUID, event: EventBase) -> None:
        """Execute any applicable callbacks for the event and store the results."""
        return None
