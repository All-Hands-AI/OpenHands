from abc import ABC, abstractmethod

from openhands.events.stream import EventStream
from openhands.server.session.conversation import Conversation
from openhands.server.settings import Settings


class ConversationManager(ABC):
    @abstractmethod
    async def __aenter__(self):
        """Begin using the SessionManager"""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Finish using the SessionManager"""

    @abstractmethod
    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        """Attach the manager to a conversation by id"""

    @abstractmethod
    async def join_conversation(
        self, sid: str, connection_id: str, settings: Settings, user_id: str | None
    ):
        """Join a conversation"""

    @abstractmethod
    async def detach_from_conversation(self, conversation: Conversation):
        """Detach from a conversation"""

    async def is_agent_loop_running(self, sid: str) -> bool:
        sids = await self.get_running_agent_loops(filter_to_sids={sid})
        return bool(sids)

    @abstractmethod
    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get the running conversation ids. If a user is supplied, then the results are limited to conversation ids for that user. If a set of filter_to_sids is supplied, then results are limited to these ids of interest."""

    @abstractmethod
    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        """Get the connection ids mapped to conversation ids.  If a user is supplied, then the results are limited to conversation ids for that user. If a set of filter_to_sids is supplied, then results are limited to these ids of interest."""

    @abstractmethod
    async def maybe_start_agent_loop(
        self, sid: str, settings: Settings, user_id: str | None
    ) -> EventStream:
        """Start an agent loop if it is not currently running and return the event stream for it."""

    @abstractmethod
    async def send_to_event_stream(self, connection_id: str, data: dict):
        """Send an event to an event stream"""

    @abstractmethod
    async def disconnect_from_conversation(self, connection_id: str):
        """Disconnect from a conversation"""

    @abstractmethod
    async def close_conversation(self, sid: str):
        """Close a conversation"""
