import asyncio
import json
import time
from dataclasses import dataclass, field
from uuid import uuid4

import socketio

from openhands.core.config import AppConfig
from openhands.core.exceptions import AgentRuntimeUnavailableError
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStream, session_exists
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import ROOM_KEY, Session
from openhands.server.settings import Settings
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.shutdown_listener import should_continue

_REDIS_POLL_TIMEOUT = 1.5
_CHECK_ALIVE_INTERVAL = 15

_CLEANUP_INTERVAL = 15
_CLEANUP_EXCEPTION_WAIT_TIME = 15


class ConversationDoesNotExistError(Exception):
    pass


@dataclass
class _SessionIsRunningCheck:
    request_id: str
    request_sids: list[str]
    running_sids: set[str] = field(default_factory=set)
    flag: asyncio.Event = field(default_factory=asyncio.Event)


@dataclass
class SessionManager:
    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore
    _local_agent_loops_by_sid: dict[str, Session] = field(default_factory=dict)
    local_connection_id_to_session_id: dict[str, str] = field(default_factory=dict)
    _last_alive_timestamps: dict[str, float] = field(default_factory=dict)
    _redis_listen_task: asyncio.Task | None = None
    _session_is_running_checks: dict[str, _SessionIsRunningCheck] = field(
        default_factory=dict
    )
    _active_conversations: dict[str, tuple[Conversation, int]] = field(
        default_factory=dict
    )
    _detached_conversations: dict[str, tuple[Conversation, float]] = field(
        default_factory=dict
    )
    _conversations_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _cleanup_task: asyncio.Task | None = None
    _has_remote_connections_flags: dict[str, asyncio.Event] = field(
        default_factory=dict
    )

    async def __aenter__(self):
        redis_client = self._get_redis_client()
        if redis_client:
            self._redis_listen_task = asyncio.create_task(self._redis_subscribe())
        self._cleanup_task = asyncio.create_task(self._cleanup_detached_conversations())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._redis_listen_task:
            self._redis_listen_task.cancel()
            self._redis_listen_task = None
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    def _get_redis_client(self):
        redis_client = getattr(self.sio.manager, 'redis', None)
        return redis_client

    async def _redis_subscribe(self):
        """
        We use a redis backchannel to send actions between server nodes
        """
        logger.debug('_redis_subscribe')
        redis_client = self._get_redis_client()
        pubsub = redis_client.pubsub()
        await pubsub.subscribe('oh_event')
        while should_continue():
            try:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=5
                )
                if message:
                    await self._process_message(message)
            except asyncio.CancelledError:
                return
            except Exception:
                try:
                    asyncio.get_running_loop()
                    logger.warning(
                        'error_reading_from_redis', exc_info=True, stack_info=True
                    )
                except RuntimeError:
                    return  # Loop has been shut down

    async def _process_message(self, message: dict):
        data = json.loads(message['data'])
        logger.debug(f'got_published_message:{message}')
        message_type = data['message_type']
        if message_type == 'event':
            sid = data['sid']
            session = self._local_agent_loops_by_sid.get(sid)
            if session:
                await session.dispatch(data['data'])
        elif message_type == 'is_session_running':
            # Another node in the cluster is asking if the current node is running the session given.
            request_id = data['request_id']
            sids = [
                sid for sid in data['sids'] if sid in self._local_agent_loops_by_sid
            ]
            if sids:
                await self._get_redis_client().publish(
                    'oh_event',
                    json.dumps(
                        {
                            'request_id': request_id,
                            'sids': sids,
                            'message_type': 'session_is_running',
                        }
                    ),
                )
        elif message_type == 'session_is_running':
            request_id = data['request_id']
            for sid in data['sids']:
                self._last_alive_timestamps[sid] = time.time()
            check = self._session_is_running_checks.get(request_id)
            if check:
                check.running_sids.update(data['sids'])
                if len(check.request_sids) == len(check.running_sids):
                    check.flag.set()
        elif message_type == 'has_remote_connections_query':
            # Another node in the cluster is asking if the current node is connected to a session
            sid = data['sid']
            required = sid in self.local_connection_id_to_session_id.values()
            if required:
                await self._get_redis_client().publish(
                    'oh_event',
                    json.dumps(
                        {'sid': sid, 'message_type': 'has_remote_connections_response'}
                    ),
                )
        elif message_type == 'has_remote_connections_response':
            sid = data['sid']
            flag = self._has_remote_connections_flags.get(sid)
            if flag:
                flag.set()
        elif message_type == 'session_closing':
            # Session closing event - We only get this in the event of graceful shutdown,
            # which can't be guaranteed - nodes can simply vanish unexpectedly!
            sid = data['sid']
            logger.debug(f'session_closing:{sid}')
            for (
                connection_id,
                local_sid,
            ) in self.local_connection_id_to_session_id.items():
                if sid == local_sid:
                    logger.warning(
                        'local_connection_to_closing_session:{connection_id}:{sid}'
                    )
                    await self.sio.disconnect(connection_id)

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
                return None
            end_time = time.time()
            logger.info(
                f'Conversation {c.sid} connected in {end_time - start_time} seconds'
            )
            self._active_conversations[sid] = (c, 1)
            return c

    async def join_conversation(self, sid: str, connection_id: str, settings: Settings):
        logger.info(f'join_conversation:{sid}:{connection_id}')
        await self.sio.enter_room(connection_id, ROOM_KEY.format(sid=sid))
        self.local_connection_id_to_session_id[connection_id] = sid
        event_stream = await self._get_event_stream(sid)
        if not event_stream:
            return await self.maybe_start_agent_loop(sid, settings)
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

    async def _cleanup_detached_conversations(self):
        while should_continue():
            if self._get_redis_client():
                # Debug info for HA envs
                logger.info(
                    f'Attached conversations: {len(self._active_conversations)}'
                )
                logger.info(
                    f'Detached conversations: {len(self._detached_conversations)}'
                )
                logger.info(
                    f'Running agent loops: {len(self._local_agent_loops_by_sid)}'
                )
                logger.info(
                    f'Local connections: {len(self.local_connection_id_to_session_id)}'
                )
            try:
                async with self._conversations_lock:
                    # Create a list of items to process to avoid modifying dict during iteration
                    items = list(self._detached_conversations.items())
                    for sid, (conversation, detach_time) in items:
                        await conversation.disconnect()
                        self._detached_conversations.pop(sid, None)

                await asyncio.sleep(_CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                async with self._conversations_lock:
                    for conversation, _ in self._detached_conversations.values():
                        await conversation.disconnect()
                    self._detached_conversations.clear()
                return
            except Exception:
                logger.warning('error_cleaning_detached_conversations', exc_info=True)
                await asyncio.sleep(_CLEANUP_EXCEPTION_WAIT_TIME)

    async def get_agent_loop_running(self, sids: set[str]) -> set[str]:
        running_sids = set(sid for sid in sids if sid in self._local_agent_loops_by_sid)
        check_cluster_sids = [sid for sid in sids if sid not in running_sids]
        running_cluster_sids = await self.get_agent_loop_running_in_cluster(
            check_cluster_sids
        )
        running_sids.union(running_cluster_sids)
        return running_sids

    async def is_agent_loop_running(self, sid: str) -> bool:
        if await self.is_agent_loop_running_locally(sid):
            return True
        if await self.is_agent_loop_running_in_cluster(sid):
            return True
        return False

    async def is_agent_loop_running_locally(self, sid: str) -> bool:
        return sid in self._local_agent_loops_by_sid

    async def is_agent_loop_running_in_cluster(self, sid: str) -> bool:
        running_sids = await self.get_agent_loop_running_in_cluster([sid])
        return bool(running_sids)

    async def get_agent_loop_running_in_cluster(self, sids: list[str]) -> set[str]:
        """As the rest of the cluster if a session is running. Wait a for a short timeout for a reply"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return set()

        flag = asyncio.Event()
        request_id = str(uuid4())
        check = _SessionIsRunningCheck(request_id=request_id, request_sids=sids)
        self._session_is_running_checks[request_id] = check
        try:
            logger.debug(f'publish:is_session_running:{sids}')
            await redis_client.publish(
                'oh_event',
                json.dumps(
                    {
                        'request_id': request_id,
                        'sids': sids,
                        'message_type': 'is_session_running',
                    }
                ),
            )
            async with asyncio.timeout(_REDIS_POLL_TIMEOUT):
                await flag.wait()

            return check.running_sids
        except TimeoutError:
            # Nobody replied in time
            return check.running_sids
        finally:
            self._session_is_running_checks.pop(request_id, None)

    async def _has_remote_connections(self, sid: str) -> bool:
        """As the rest of the cluster if they still want this session running. Wait a for a short timeout for a reply"""
        # Create a flag for the callback
        flag = asyncio.Event()
        self._has_remote_connections_flags[sid] = flag
        try:
            await self._get_redis_client().publish(
                'oh_event',
                json.dumps(
                    {
                        'sid': sid,
                        'message_type': 'has_remote_connections_query',
                    }
                ),
            )
            async with asyncio.timeout(_REDIS_POLL_TIMEOUT):
                await flag.wait()

            result = flag.is_set()
            return result
        except TimeoutError:
            # Nobody replied in time
            return False
        finally:
            self._has_remote_connections_flags.pop(sid, None)

    async def maybe_start_agent_loop(self, sid: str, settings: Settings) -> EventStream:
        logger.info(f'maybe_start_agent_loop:{sid}')
        session: Session | None = None
        if not await self.is_agent_loop_running(sid):
            logger.info(f'start_agent_loop:{sid}')
            session = Session(
                sid=sid, file_store=self.file_store, config=self.config, sio=self.sio
            )
            self._local_agent_loops_by_sid[sid] = session
            asyncio.create_task(session.initialize_agent(settings))

        event_stream = await self._get_event_stream(sid)
        if not event_stream:
            logger.error(f'No event stream after starting agent loop: {sid}')
            raise RuntimeError(f'no_event_stream:{sid}')
        asyncio.create_task(self._cleanup_session_later(sid))
        return event_stream

    async def _get_event_stream(self, sid: str) -> EventStream | None:
        logger.info(f'_get_event_stream:{sid}')
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            logger.info(f'found_local_agent_loop:{sid}')
            return session.agent_session.event_stream

        if await self.is_agent_loop_running_in_cluster(sid):
            logger.info(f'found_remote_agent_loop:{sid}')
            return EventStream(sid, self.file_store)

        return None

    async def send_to_event_stream(self, connection_id: str, data: dict):
        # If there is a local session running, send to that
        sid = self.local_connection_id_to_session_id.get(connection_id)
        if not sid:
            raise RuntimeError(f'no_connected_session:{connection_id}')

        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            await session.dispatch(data)
            return

        redis_client = self._get_redis_client()
        if redis_client:
            # If we have a recent report that the session is alive in another pod
            last_alive_at = self._last_alive_timestamps.get(sid) or 0
            next_alive_check = last_alive_at + _CHECK_ALIVE_INTERVAL
            if (
                next_alive_check > time.time()
                or await self.is_agent_loop_running_in_cluster(sid)
            ):
                # Send the event to the other pod
                await redis_client.publish(
                    'oh_event',
                    json.dumps(
                        {
                            'sid': sid,
                            'message_type': 'event',
                            'data': data,
                        }
                    ),
                )
                return

        raise RuntimeError(f'no_connected_session:{connection_id}:{sid}')

    async def disconnect_from_session(self, connection_id: str):
        sid = self.local_connection_id_to_session_id.pop(connection_id, None)
        logger.info(f'disconnect_from_session:{connection_id}:{sid}')
        if not sid:
            # This can occur if the init action was never run.
            logger.warning(f'disconnect_from_uninitialized_session:{connection_id}')
            return

        if should_continue():
            asyncio.create_task(self._cleanup_session_later(sid))
        else:
            await self._close_session(sid)

    async def _cleanup_session_later(self, sid: str):
        # Once there have been no connections to a session for a reasonable period, we close it
        try:
            await asyncio.sleep(self.config.sandbox.close_delay)
        finally:
            # If the sleep was cancelled, we still want to close these
            await self._cleanup_session(sid)

    async def _cleanup_session(self, sid: str) -> bool:
        # Get local connections
        logger.info(f'_cleanup_session:{sid}')
        has_local_connections = next(
            (True for v in self.local_connection_id_to_session_id.values() if v == sid),
            False,
        )
        if has_local_connections:
            return False

        # If no local connections, get connections through redis
        redis_client = self._get_redis_client()
        if redis_client and await self._has_remote_connections(sid):
            return False

        # We alert the cluster in case they are interested
        if redis_client:
            await redis_client.publish(
                'oh_event',
                json.dumps({'sid': sid, 'message_type': 'session_closing'}),
            )

        await self._close_session(sid)
        return True

    async def _close_session(self, sid: str):
        logger.info(f'_close_session:{sid}')

        # Clear up local variables
        connection_ids_to_remove = list(
            connection_id
            for connection_id, conn_sid in self.local_connection_id_to_session_id.items()
            if sid == conn_sid
        )
        logger.info(f'removing connections: {connection_ids_to_remove}')
        for connnnection_id in connection_ids_to_remove:
            self.local_connection_id_to_session_id.pop(connnnection_id, None)

        session = self._local_agent_loops_by_sid.pop(sid, None)
        if not session:
            logger.warning(f'no_session_to_close:{sid}')
            return

        logger.info(f'closing_session:{session.sid}')
        # We alert the cluster in case they are interested
        redis_client = self._get_redis_client()
        if redis_client:
            await redis_client.publish(
                'oh_event',
                json.dumps({'sid': session.sid, 'message_type': 'session_closing'}),
            )

        await call_sync_from_async(session.close)
        logger.info(f'closed_session:{session.sid}')
