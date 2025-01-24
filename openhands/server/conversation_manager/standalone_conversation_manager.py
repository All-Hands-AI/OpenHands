import asyncio
import time
from dataclasses import dataclass, field
from typing import Iterable

import socketio

from openhands.core.config.app_config import AppConfig
from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.events.action import MessageAction
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

    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore
    _local_agent_loops_by_sid: dict[str, Session] = field(default_factory=dict)
    _local_connection_id_to_session_id: dict[str, str] = field(default_factory=dict)
    _active_conversations: dict[str, tuple[Conversation, int]] = field(
        default_factory=dict
    )
    _detached_conversations: dict[str, tuple[Conversation, float]] = field(
        default_factory=dict
    )
    _conversations_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _cleanup_task: asyncio.Task | None = None

    async def __aenter__(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_stale())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def attach_to_conversation(self, sid: str) -> Conversation | None:
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
            logger.info(
                f'Conversation {c.sid} connected in {end_time - start_time} seconds'
            )
            self._active_conversations[sid] = (c, 1)
            return c

    async def join_conversation(
        self, sid: str, connection_id: str, settings: Settings, user_id: str | None
    ):
        logger.info(f'join_conversation:{sid}:{connection_id}')
        await self.sio.enter_room(connection_id, ROOM_KEY.format(sid=sid))
        self._local_connection_id_to_session_id[connection_id] = sid
        event_stream = await self._get_event_stream(sid)
        if not event_stream:
            return await self.maybe_start_agent_loop(sid, settings, user_id)
        return event_stream

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

                connections = await self.get_connections(
                    filter_to_sids=set(sid_to_close)
                )
                connected_sids = {sid for _, sid in connections.items()}
                sid_to_close = [
                    sid for sid in sid_to_close if sid not in connected_sids
                ]
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

    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get the running session ids. If a user is supplied, then the results are limited to session ids for that user. If a set of filter_to_sids is supplied, then results are limited to these ids of interest."""
        items: Iterable[tuple[str, Session]] = self._local_agent_loops_by_sid.items()
        if filter_to_sids is not None:
            items = (item for item in items if item[0] in filter_to_sids)
        if user_id:
            items = (item for item in items if item[1].user_id == user_id)
        sids = {sid for sid, _ in items}
        return sids

    async def get_connections(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        connections = dict(**self._local_connection_id_to_session_id)
        if filter_to_sids is not None:
            connections = {
                connection_id: sid
                for connection_id, sid in connections.items()
                if sid in filter_to_sids
            }
        if user_id:
            for connection_id, sid in list(connections.items()):
                session = self._local_agent_loops_by_sid.get(sid)
                if not session or session.user_id != user_id:
                    connections.pop(connection_id)
        return connections

    async def maybe_start_agent_loop(
        self,
        sid: str,
        settings: Settings,
        user_id: str | None,
        initial_user_msg: MessageAction | None = None,
    ) -> EventStream:
        logger.info(f'maybe_start_agent_loop:{sid}')
        session: Session | None = None
        if not await self.is_agent_loop_running(sid):
            logger.info(f'start_agent_loop:{sid}')

            response_ids = await self.get_running_agent_loops(user_id)
            if len(response_ids) >= MAX_RUNNING_CONVERSATIONS:
                logger.info('too_many_sessions_for:{user_id}')
                # Order is not guaranteed, but response_ids tend to be in descending chronological order
                # By reversing, we are likely to pick the oldest (or at least an older) conversation
                session_id = next(iter(reversed(list(response_ids))))
                await self.close_session(session_id)

            session = Session(
                sid=sid,
                file_store=self.file_store,
                config=self.config,
                sio=self.sio,
                user_id=user_id,
            )
            self._local_agent_loops_by_sid[sid] = session
            asyncio.create_task(session.initialize_agent(settings, initial_user_msg))

        event_stream = await self._get_event_stream(sid)
        if not event_stream:
            logger.error(f'No event stream after starting agent loop: {sid}')
            raise RuntimeError(f'no_event_stream:{sid}')
        return event_stream

    async def _get_event_stream(self, sid: str) -> EventStream | None:
        logger.info(f'_get_event_stream:{sid}')
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            logger.info(f'found_local_agent_loop:{sid}')
            return session.agent_session.event_stream
        return None

    async def send_to_event_stream(self, connection_id: str, data: dict):
        # If there is a local session running, send to that
        sid = self._local_connection_id_to_session_id.get(connection_id)
        if not sid:
            raise RuntimeError(f'no_connected_session:{connection_id}')

        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            await session.dispatch(data)
            return

        raise RuntimeError(f'no_connected_session:{connection_id}:{sid}')

    async def disconnect_from_session(self, connection_id: str):
        sid = self._local_connection_id_to_session_id.pop(connection_id, None)
        logger.info(f'disconnect_from_session:{connection_id}:{sid}')
        if not sid:
            # This can occur if the init action was never run.
            logger.warning(f'disconnect_from_uninitialized_session:{connection_id}')
            return

    async def close_session(self, sid: str):
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            await self._close_session(sid)

    async def _close_session(self, sid: str):
        logger.info(f'_close_session:{sid}')

        # Clear up local variables
        connection_ids_to_remove = list(
            connection_id
            for connection_id, conn_sid in self._local_connection_id_to_session_id.items()
            if sid == conn_sid
        )
        logger.info(f'removing connections: {connection_ids_to_remove}')
        for connnnection_id in connection_ids_to_remove:
            self._local_connection_id_to_session_id.pop(connnnection_id, None)

        session = self._local_agent_loops_by_sid.pop(sid, None)
        if not session:
            logger.warning(f'no_session_to_close:{sid}')
            return

        logger.info(f'closing_session:{session.sid}')
        await session.close()
        logger.info(f'closed_session:{session.sid}')

    @classmethod
    def get_instance(
        cls,
        sio: socketio.AsyncServer,
        config: AppConfig,
        file_store: FileStore,
    ) -> ConversationManager:
        return StandaloneConversationManager(sio, config, file_store)
