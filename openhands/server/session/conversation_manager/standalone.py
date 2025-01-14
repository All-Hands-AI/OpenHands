import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple

import socketio

from openhands.core.config import AppConfig
from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.events.stream import EventStream, session_exists
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import ROOM_KEY, Session
from openhands.server.settings import Settings
from openhands.storage.files import FileStore
from openhands.utils.async_utils import wait_all
from openhands.utils.shutdown_listener import should_continue

from .conversation_manager import ConversationManager

_CLEANUP_INTERVAL = 15
MAX_RUNNING_CONVERSATIONS = 3


@dataclass
class StandaloneConversationManager(ConversationManager):
    """Manages conversations in standalone mode (single server instance)."""

    _local_agent_loops_by_sid: dict[str, Session] = field(default_factory=dict)
    _local_connection_id_to_session_id: dict[str, str] = field(default_factory=dict)
    _active_conversations: dict[str, Tuple[Conversation, int]] = field(default_factory=dict)
    _detached_conversations: dict[str, Tuple[Conversation, float]] = field(default_factory=dict)
    _conversations_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _cleanup_task: Optional[asyncio.Task] = field(default=None)

    async def __aenter__(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_stale())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def attach_to_conversation(self, sid: str) -> Optional[Conversation]:
        start_time = time.time()
        if not await session_exists(sid, self.file_store):
            return None

        async with self._conversations_lock:
            # Check if we have an active conversation we can reuse
            if sid in self._active_conversations:
                conversation, count = self._active_conversations[sid]
                self._active_conversations[sid] = (conversation, count + 1)
                logger.info(f'Reusing active conversation {sid}')
                return conversation

            # Check if we have a detached conversation we can reuse
            if sid in self._detached_conversations:
                conversation, _ = self._detached_conversations.pop(sid)
                self._active_conversations[sid] = (conversation, 1)
                logger.info(f'Reusing detached conversation {sid}')
                return conversation

            # Create new conversation if none exists
            c = Conversation(sid, file_store=self.file_store, config=self.config)
            try:
                await c.connect()
            except AgentRuntimeUnavailableError as e:
                logger.error(f'Error connecting to conversation {c.sid}: {e}')
                await c.disconnect()
                return None
            end_time = time.time()
            logger.info(f'Conversation {c.sid} connected in {end_time - start_time} seconds')
            self._active_conversations[sid] = (c, 1)
            return c

    async def detach_from_conversation(self, conversation: Conversation):
        sid = conversation.sid
        async with self._conversations_lock:
            if sid in self._active_conversations:
                conv, count = self._active_conversations[sid]
                if count > 1:
                    self._active_conversations[sid] = (conv, count - 1)
                    return
                else:
                    self._active_conversations.pop(sid)
                    self._detached_conversations[sid] = (conversation, time.time())

    async def join_conversation(
        self, sid: str, connection_id: str, settings: Settings, user_id: Optional[str]
    ) -> Optional[EventStream]:
        logger.info(f'join_conversation:{sid}:{connection_id}')
        await self.sio.enter_room(connection_id, ROOM_KEY.format(sid=sid))
        self._local_connection_id_to_session_id[connection_id] = sid
        event_stream = await self._get_event_stream(sid)
        if not event_stream:
            return await self._maybe_start_agent_loop(sid, settings, user_id)
        return event_stream

    async def is_agent_loop_running(self, sid: str) -> bool:
        return sid in self._local_agent_loops_by_sid

    async def get_running_agent_loops(
        self, user_id: Optional[str] = None, filter_to_sids: Optional[set[str]] = None
    ) -> set[str]:
        items = self._local_agent_loops_by_sid.items()
        if filter_to_sids is not None:
            items = ((sid, session) for sid, session in items if sid in filter_to_sids)
        if user_id:
            items = ((sid, session) for sid, session in items if session.user_id == user_id)
        return {sid for sid, _ in items}

    async def get_connections(
        self, user_id: Optional[str] = None, filter_to_sids: Optional[set[str]] = None
    ) -> dict[str, str]:
        items = self._local_connection_id_to_session_id.items()
        if filter_to_sids is not None:
            items = ((cid, sid) for cid, sid in items if sid in filter_to_sids)
        if user_id:
            items = (
                (cid, sid)
                for cid, sid in items
                if self._local_agent_loops_by_sid.get(sid, Session(None, None)).user_id == user_id
            )
        return dict(items)

    async def send_to_event_stream(self, connection_id: str, data: dict):
        sid = self._local_connection_id_to_session_id.get(connection_id)
        if not sid:
            return
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            await session.dispatch(data)

    async def disconnect_from_session(self, connection_id: str):
        sid = self._local_connection_id_to_session_id.pop(connection_id, None)
        if sid:
            await self.sio.leave_room(connection_id, ROOM_KEY.format(sid=sid))

    async def close_session(self, sid: str):
        await self._close_session(sid)

    async def _cleanup_stale(self):
        while should_continue():
            try:
                async with self._conversations_lock:
                    # Create a list of items to process to avoid modifying dict during iteration
                    items = list(self._detached_conversations.items())
                    for sid, (conversation, detach_time) in items:
                        await conversation.disconnect()
                        self._detached_conversations.pop(sid, None)

                close_threshold = time.time() - self.config.sandbox.close_delay
                running_loops = list(self._local_agent_loops_by_sid.items())
                running_loops.sort(key=lambda item: item[1].last_active_ts)
                sid_to_close: list[str] = []
                for sid, session in running_loops:
                    state = session.agent_session.get_state()
                    if session.last_active_ts < close_threshold and state not in [
                        AgentState.RUNNING,
                        None,
                    ]:
                        sid_to_close.append(sid)

                connections = await self.get_connections(filter_to_sids=set(sid_to_close))
                connected_sids = {sid for _, sid in connections.items()}
                sid_to_close = [sid for sid in sid_to_close if sid not in connected_sids]

                await wait_all(self._close_session(sid) for sid in sid_to_close)
                await asyncio.sleep(_CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                async with self._conversations_lock:
                    for conversation, _ in self._detached_conversations.values():
                        await conversation.disconnect()
                    self._detached_conversations.clear()
                await wait_all(
                    self._close_session(sid) for sid in self._local_agent_loops_by_sid
                )
                return
            except Exception as e:
                logger.warning(f'error_cleaning_stale: {str(e)}')
                await asyncio.sleep(_CLEANUP_INTERVAL)

    async def _get_event_stream(self, sid: str) -> Optional[EventStream]:
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            return session.event_stream
        return None

    async def _maybe_start_agent_loop(
        self, sid: str, settings: Settings, user_id: Optional[str]
    ) -> Optional[EventStream]:
        if sid in self._local_agent_loops_by_sid:
            return self._local_agent_loops_by_sid[sid].event_stream

        session = Session(user_id, settings)
        event_stream = await session.start(sid, self.file_store)
        if event_stream:
            self._local_agent_loops_by_sid[sid] = session
            return event_stream
        return None

    async def _close_session(self, sid: str):
        session = self._local_agent_loops_by_sid.pop(sid, None)
        if session:
            await session.close()
            # Create a list of items to process to avoid modifying dict during iteration
            items = list(self._local_connection_id_to_session_id.items())
            for connection_id, local_sid in items:
                if sid == local_sid:
                    await self.sio.disconnect(connection_id)