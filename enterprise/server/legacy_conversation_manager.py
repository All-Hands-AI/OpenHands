from __future__ import annotations

import time
from dataclasses import dataclass, field

import socketio
from server.clustered_conversation_manager import ClusteredConversationManager
from server.saas_nested_conversation_manager import SaasNestedConversationManager

from openhands.core.config import LLMConfig, OpenHandsConfig
from openhands.events.action import MessageAction
from openhands.server.config.server_config import ServerConfig
from openhands.server.conversation_manager.conversation_manager import (
    ConversationManager,
)
from openhands.server.data_models.agent_loop_info import AgentLoopInfo
from openhands.server.monitoring import MonitoringListener
from openhands.server.session.conversation import ServerConversation
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore
from openhands.utils.async_utils import wait_all

_LEGACY_ENTRY_TIMEOUT_SECONDS = 3600


@dataclass
class LegacyCacheEntry:
    """Cache entry for legacy mode status."""

    is_legacy: bool
    timestamp: float


@dataclass
class LegacyConversationManager(ConversationManager):
    """
    Conversation manager for use while migrating - since existing conversations are not nested!
    Separate class from SaasNestedConversationManager so it can be easliy removed in a few weeks.
    (As of 2025-07-23)
    """

    sio: socketio.AsyncServer
    config: OpenHandsConfig
    server_config: ServerConfig
    file_store: FileStore
    conversation_manager: SaasNestedConversationManager
    legacy_conversation_manager: ClusteredConversationManager
    _legacy_cache: dict[str, LegacyCacheEntry] = field(default_factory=dict)

    async def __aenter__(self):
        await wait_all(
            [
                self.conversation_manager.__aenter__(),
                self.legacy_conversation_manager.__aenter__(),
            ]
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await wait_all(
            [
                self.conversation_manager.__aexit__(exc_type, exc_value, traceback),
                self.legacy_conversation_manager.__aexit__(
                    exc_type, exc_value, traceback
                ),
            ]
        )

    async def request_llm_completion(
        self,
        sid: str,
        service_id: str,
        llm_config: LLMConfig,
        messages: list[dict[str, str]],
    ) -> str:
        session = self.get_agent_session(sid)
        llm_registry = session.llm_registry
        return llm_registry.request_extraneous_completion(
            service_id, llm_config, messages
        )

    async def attach_to_conversation(
        self, sid: str, user_id: str | None = None
    ) -> ServerConversation | None:
        if await self.should_start_in_legacy_mode(sid):
            return await self.legacy_conversation_manager.attach_to_conversation(
                sid, user_id
            )
        return await self.conversation_manager.attach_to_conversation(sid, user_id)

    async def detach_from_conversation(self, conversation: ServerConversation):
        if await self.should_start_in_legacy_mode(conversation.sid):
            return await self.legacy_conversation_manager.detach_from_conversation(
                conversation
            )
        return await self.conversation_manager.detach_from_conversation(conversation)

    async def join_conversation(
        self,
        sid: str,
        connection_id: str,
        settings: Settings,
        user_id: str | None,
    ) -> AgentLoopInfo:
        if await self.should_start_in_legacy_mode(sid):
            return await self.legacy_conversation_manager.join_conversation(
                sid, connection_id, settings, user_id
            )
        return await self.conversation_manager.join_conversation(
            sid, connection_id, settings, user_id
        )

    def get_agent_session(self, sid: str):
        session = self.legacy_conversation_manager.get_agent_session(sid)
        if session is None:
            session = self.conversation_manager.get_agent_session(sid)
        return session

    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        if filter_to_sids and len(filter_to_sids) == 1:
            sid = next(iter(filter_to_sids))
            if await self.should_start_in_legacy_mode(sid):
                return await self.legacy_conversation_manager.get_running_agent_loops(
                    user_id, filter_to_sids
                )
            return await self.conversation_manager.get_running_agent_loops(
                user_id, filter_to_sids
            )

        # Get all running agent loops from both managers
        agent_loops, legacy_agent_loops = await wait_all(
            [
                self.conversation_manager.get_running_agent_loops(
                    user_id, filter_to_sids
                ),
                self.legacy_conversation_manager.get_running_agent_loops(
                    user_id, filter_to_sids
                ),
            ]
        )

        # Combine the results
        result = set()
        for sid in legacy_agent_loops:
            if await self.should_start_in_legacy_mode(sid):
                result.add(sid)

        for sid in agent_loops:
            if not await self.should_start_in_legacy_mode(sid):
                result.add(sid)

        return result

    async def is_agent_loop_running(self, sid: str) -> bool:
        return bool(await self.get_running_agent_loops(filter_to_sids={sid}))

    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        if filter_to_sids and len(filter_to_sids) == 1:
            sid = next(iter(filter_to_sids))
            if await self.should_start_in_legacy_mode(sid):
                return await self.legacy_conversation_manager.get_connections(
                    user_id, filter_to_sids
                )
            return await self.conversation_manager.get_connections(
                user_id, filter_to_sids
            )
        agent_loops, legacy_agent_loops = await wait_all(
            [
                self.conversation_manager.get_connections(user_id, filter_to_sids),
                self.legacy_conversation_manager.get_connections(
                    user_id, filter_to_sids
                ),
            ]
        )
        legacy_agent_loops.update(agent_loops)
        return legacy_agent_loops

    async def maybe_start_agent_loop(
        self,
        sid: str,
        settings: Settings,
        user_id: str,  # type: ignore[override]
        initial_user_msg: MessageAction | None = None,
        replay_json: str | None = None,
    ) -> AgentLoopInfo:
        if await self.should_start_in_legacy_mode(sid):
            return await self.legacy_conversation_manager.maybe_start_agent_loop(
                sid, settings, user_id, initial_user_msg, replay_json
            )
        return await self.conversation_manager.maybe_start_agent_loop(
            sid, settings, user_id, initial_user_msg, replay_json
        )

    async def send_to_event_stream(self, connection_id: str, data: dict):
        return await self.legacy_conversation_manager.send_to_event_stream(
            connection_id, data
        )

    async def send_event_to_conversation(self, sid: str, data: dict):
        if await self.should_start_in_legacy_mode(sid):
            await self.legacy_conversation_manager.send_event_to_conversation(sid, data)
        await self.conversation_manager.send_event_to_conversation(sid, data)

    async def disconnect_from_session(self, connection_id: str):
        return await self.legacy_conversation_manager.disconnect_from_session(
            connection_id
        )

    async def close_session(self, sid: str):
        if await self.should_start_in_legacy_mode(sid):
            await self.legacy_conversation_manager.close_session(sid)
        await self.conversation_manager.close_session(sid)

    async def get_agent_loop_info(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> list[AgentLoopInfo]:
        if filter_to_sids and len(filter_to_sids) == 1:
            sid = next(iter(filter_to_sids))
            if await self.should_start_in_legacy_mode(sid):
                return await self.legacy_conversation_manager.get_agent_loop_info(
                    user_id, filter_to_sids
                )
            return await self.conversation_manager.get_agent_loop_info(
                user_id, filter_to_sids
            )
        agent_loops, legacy_agent_loops = await wait_all(
            [
                self.conversation_manager.get_agent_loop_info(user_id, filter_to_sids),
                self.legacy_conversation_manager.get_agent_loop_info(
                    user_id, filter_to_sids
                ),
            ]
        )

        # Combine results
        result = []
        legacy_sids = set()

        # Add legacy agent loops
        for agent_loop in legacy_agent_loops:
            if await self.should_start_in_legacy_mode(agent_loop.conversation_id):
                result.append(agent_loop)
                legacy_sids.add(agent_loop.conversation_id)

        # Add non-legacy agent loops
        for agent_loop in agent_loops:
            if (
                agent_loop.conversation_id not in legacy_sids
                and not await self.should_start_in_legacy_mode(
                    agent_loop.conversation_id
                )
            ):
                result.append(agent_loop)

        return result

    def _cleanup_expired_cache_entries(self):
        """Remove expired entries from the local cache."""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._legacy_cache.items()
            if current_time - entry.timestamp > _LEGACY_ENTRY_TIMEOUT_SECONDS
        ]
        for key in expired_keys:
            del self._legacy_cache[key]

    async def should_start_in_legacy_mode(self, conversation_id: str) -> bool:
        """
        Check if a conversation should run in legacy mode by directly checking the runtime.
        The /list method does not include stopped conversations even though the PVC for these
        may not yet have been deleted, so we need to check /sessions/{session_id} directly.
        """
        # Clean up expired entries periodically
        self._cleanup_expired_cache_entries()

        # First check the local cache
        if conversation_id in self._legacy_cache:
            cached_entry = self._legacy_cache[conversation_id]
            # Check if the cached value is still valid
            if time.time() - cached_entry.timestamp <= _LEGACY_ENTRY_TIMEOUT_SECONDS:
                return cached_entry.is_legacy

        # If not in cache or expired, check the runtime directly
        runtime = await self.conversation_manager._get_runtime(conversation_id)
        is_legacy = self.is_legacy_runtime(runtime)

        # Cache the result with current timestamp
        self._legacy_cache[conversation_id] = LegacyCacheEntry(is_legacy, time.time())

        return is_legacy

    def is_legacy_runtime(self, runtime: dict | None) -> bool:
        """
        Determine if a runtime is a legacy runtime based on its command.

        Args:
            runtime: The runtime dictionary or None if not found

        Returns:
            bool: True if this is a legacy runtime, False otherwise
        """
        if runtime is None:
            return False
        return 'openhands.server' not in runtime['command']

    @classmethod
    def get_instance(
        cls,
        sio: socketio.AsyncServer,
        config: OpenHandsConfig,
        file_store: FileStore,
        server_config: ServerConfig,
        monitoring_listener: MonitoringListener,
    ) -> ConversationManager:
        return LegacyConversationManager(
            sio=sio,
            config=config,
            server_config=server_config,
            file_store=file_store,
            conversation_manager=SaasNestedConversationManager.get_instance(
                sio, config, file_store, server_config, monitoring_listener
            ),
            legacy_conversation_manager=ClusteredConversationManager.get_instance(
                sio, config, file_store, server_config, monitoring_listener
            ),
        )
