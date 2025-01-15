from abc import ABC, abstractmethod

import socketio

from openhands.core.config import AppConfig
from openhands.events.stream import EventStream
from openhands.server.session.conversation import Conversation
from openhands.server.settings import Settings
from openhands.storage.files import FileStore


class ConversationManager(ABC):
    """Abstract base class for managing conversations in OpenHands.

    This class defines the interface for managing conversations, whether in standalone
    or clustered mode. It handles the lifecycle of conversations, including creation,
    attachment, detachment, and cleanup.
    """

    def __init__(
        self, sio: socketio.AsyncServer, config: AppConfig, file_store: FileStore
    ):
        self.sio = sio
        self.config = config
        self.file_store = file_store

    @abstractmethod
    async def __aenter__(self):
        """Initialize the conversation manager."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up the conversation manager."""
        pass

    @abstractmethod
    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        """Attach to an existing conversation or create a new one."""
        pass

    @abstractmethod
    async def detach_from_conversation(self, conversation: Conversation):
        """Detach from a conversation."""
        pass

    @abstractmethod
    async def join_conversation(
        self, sid: str, connection_id: str, settings: Settings, user_id: str | None
    ) -> EventStream | None:
        """Join a conversation and return its event stream."""
        pass

    async def is_agent_loop_running(self, sid: str) -> bool:
        """Check if an agent loop is running for the given session ID."""
        sids = await self.get_running_agent_loops(filter_to_sids={sid})
        return bool(sids)

    @abstractmethod
    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get all running agent loops, optionally filtered by user ID and session IDs."""
        pass

    @abstractmethod
    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        """Get all connections, optionally filtered by user ID and session IDs."""
        pass

    @abstractmethod
    async def send_to_event_stream(self, connection_id: str, data: dict):
        """Send data to an event stream."""
        pass

    @abstractmethod
    async def disconnect_from_session(self, connection_id: str):
        """Disconnect from a session."""
        pass

    @abstractmethod
    async def close_session(self, sid: str):
        """Close a session."""
        pass
