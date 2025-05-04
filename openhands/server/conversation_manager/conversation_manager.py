from __future__ import annotations

from abc import ABC, abstractmethod

import socketio

from openhands.core.config import AppConfig
from openhands.events.action import MessageAction
from openhands.events.event_store import EventStore
from openhands.server.config.server_config import ServerConfig
from openhands.server.monitoring import MonitoringListener
from openhands.server.session.conversation import Conversation
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore


class ConversationManager(ABC):
    """Abstract base class for managing conversations in OpenHands.

    This class defines the interface for managing conversations, whether in standalone
    or clustered mode. It handles the lifecycle of conversations, including creation,
    attachment, detachment, and cleanup.
    """

    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore
    conversation_store: ConversationStore

    @abstractmethod
    async def __aenter__(self):
        """Initialize the conversation manager."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up the conversation manager."""

    @abstractmethod
    async def attach_to_conversation(
        self, sid: str, user_id: str | None = None
    ) -> Conversation | None:
        """Attach to an existing conversation or create a new one."""

    @abstractmethod
    async def detach_from_conversation(self, conversation: Conversation):
        """Detach from a conversation."""

    @abstractmethod
    async def join_conversation(
        self,
        sid: str,
        connection_id: str,
        settings: Settings,
        user_id: str | None,
        github_user_id: str | None,
    ) -> EventStore | None:
        """Join a conversation and return its event stream."""

    async def is_agent_loop_running(self, sid: str) -> bool:
        """Check if an agent loop is running for the given session ID."""
        sids = await self.get_running_agent_loops(filter_to_sids={sid})
        return bool(sids)

    @abstractmethod
    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get all running agent loops, optionally filtered by user ID and session IDs."""

    @abstractmethod
    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        """Get all connections, optionally filtered by user ID and session IDs."""

    @abstractmethod
    async def maybe_start_agent_loop(
        self,
        sid: str,
        settings: Settings,
        user_id: str | None,
        initial_user_msg: MessageAction | None = None,
        replay_json: str | None = None,
        github_user_id: str | None = None,
    ) -> EventStore:
        """Start an event loop if one is not already running"""

    @abstractmethod
    async def send_to_event_stream(self, connection_id: str, data: dict):
        """Send data to an event stream."""

    @abstractmethod
    async def disconnect_from_session(self, connection_id: str):
        """Disconnect from a session."""

    @abstractmethod
    async def close_session(self, sid: str):
        """Close a session."""

    @classmethod
    @abstractmethod
    def get_instance(
        cls,
        sio: socketio.AsyncServer,
        config: AppConfig,
        file_store: FileStore,
        server_config: ServerConfig,
        monitoring_listener: MonitoringListener,
    ) -> ConversationManager:
        """Get a conversation manager instance"""
