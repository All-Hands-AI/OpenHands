import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Iterable
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
from openhands.utils.async_utils import call_sync_from_async, wait_all
from openhands.utils.shutdown_listener import should_continue

_REDIS_POLL_TIMEOUT = 1.5
_CHECK_ALIVE_INTERVAL = 15

_CLEANUP_INTERVAL = 15
_CLEANUP_EXCEPTION_WAIT_TIME = 15
MAX_RUNNING_CONVERSATIONS = 3


class ConversationDoesNotExistError(Exception):
    pass


@dataclass
class _AgentLoopRunningCheck:
    request_id: str
    request_sids: set[str] | None
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
    _running_sid_queries: dict[str, _AgentLoopRunningCheck] = field(
        default_factory=dict
    )
    _active_conversations: dict[str, tuple[Conversation, int]] = field(
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
        self._cleanup_task = asyncio.create_task(self._cleanup_stale())
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
        elif message_type == 'running_agent_loops_query':
            # Another node in the cluster is asking if the current node is running the session given.
            request_id = data['request_id']
            sids = self.get_running_agent_loops_locally(
                data.get('user_id'), data.get('filter_to_sids')
            )
            if sids:
                await self._get_redis_client().publish(
                    'oh_event',
                    json.dumps(
                        {
                            'request_id': request_id,
                            'sids': sids,
                            'message_type': 'running_sids_response',
                        }
                    ),
                )
        elif message_type == 'running_sids_response':
            request_id = data['request_id']
            for sid in data['sids']:
                self._last_alive_timestamps[sid] = time.time()
            check = self._running_sid_queries.get(request_id)
            if check:
                check.running_sids.update(data['sids'])
                if check.request_sids is not None and len(check.request_sids) == len(
                    check.running_sids
                ):
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
        elif message_type == 'close_session':
            sid = data['sid']
            if sid in self._local_agent_loops_by_sid:
                await self._on_close_session(sid)
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
        self, sid: str, connection_id: str, settings: Settings, user_id: int
    ):
        logger.info(f'join_conversation:{sid}:{connection_id}')
        await self.sio.enter_room(connection_id, ROOM_KEY.format(sid=sid))
        self.local_connection_id_to_session_id[connection_id] = sid
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

    async def _cleanup_stale(self):
        while should_continue():
            if self._get_redis_client():
                # Debug info for HA envs
                logger.info(
                    f'Running agent loops: {len(self._local_agent_loops_by_sid)}'
                )
                logger.info(
                    f'Local connections: {len(self.local_connection_id_to_session_id)}'
                )
            try:
                close_threshold = time.time() - self.config.sandbox.close_delay
                running_loops = list(self._local_agent_loops_by_sid.items())
                running_loops.sort(key=lambda item: item[1].last_active_ts)
                sid_to_close: list[str] = []
                for sid, session in running_loops:
                    if session.last_active_ts < close_threshold:
                        sid_to_close.append(sid)

                await wait_all(self._cleanup_session(sid) for sid in sid_to_close)
                await asyncio.sleep(_CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                await wait_all(
                    self._on_close_session(sid)
                    for sid in self._local_agent_loops_by_sid
                )
                return
            except Exception:
                logger.warning('error_cleaning_stale', exc_info=True)
                await asyncio.sleep(_CLEANUP_EXCEPTION_WAIT_TIME)

    async def is_agent_loop_running(self, sid: str) -> bool:
        running_sids = await self.get_running_agent_loops(filter_to_sids={sid})
        return bool(running_sids)

    async def get_running_agent_loops(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get the running session ids. If a user is supplied, then the results are limited to session ids for that user. If a set of filter_to_sids is supplied, then results are limited to these ids of interest."""
        running_sids = await self.get_running_agent_loops_locally(
            user_id, filter_to_sids
        )
        running_sids.union(
            await self.get_running_agent_loops_in_cluster(user_id, filter_to_sids)
        )
        return running_sids

    async def get_running_agent_loops_locally(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        items: Iterable[tuple[str, Session]] = self._local_agent_loops_by_sid.items()
        if filter_to_sids is not None:
            items = (item for item in items if item[0] in filter_to_sids)
        if user_id:
            items = (item for item in items if item[1].user_id == user_id)
        sids = {sid for sid, _ in items}
        return sids

    async def get_running_agent_loops_in_cluster(
        self,
        user_id: int | None = None,
        filter_to_sids: set[str] | None = None,
    ) -> set[str]:
        """As the rest of the cluster if a session is running. Wait a for a short timeout for a reply"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return set()

        flag = asyncio.Event()
        request_id = str(uuid4())
        check = _AgentLoopRunningCheck(
            request_id=request_id, request_sids=filter_to_sids
        )
        self._running_sid_queries[request_id] = check
        try:
            logger.debug(
                f'publish:running_agent_loops_query:{user_id}:{filter_to_sids}'
            )
            data: dict = {
                'request_id': request_id,
                'message_type': 'running_agent_loops_query',
            }
            if user_id:
                data['user_id'] = user_id
            if filter_to_sids:
                data['filter_to_sids'] = list(filter_to_sids)
            await redis_client.publish('oh_event', json.dumps(data))
            async with asyncio.timeout(_REDIS_POLL_TIMEOUT):
                await flag.wait()

            return check.running_sids
        except TimeoutError:
            # Nobody replied in time
            return check.running_sids
        finally:
            self._running_sid_queries.pop(request_id, None)

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

    async def maybe_start_agent_loop(
        self, sid: str, settings: Settings, user_id: int = 0
    ) -> EventStream:
        logger.info(f'maybe_start_agent_loop:{sid}')
        session: Session | None = None
        if not await self.is_agent_loop_running(sid):
            logger.info(f'start_agent_loop:{sid}')

            running_sids = await self.get_running_agent_loops(user_id)
            if len(running_sids) > MAX_RUNNING_CONVERSATIONS:
                logger.info('too_many_sessions_for:{user_id}')
                await self.close_session(next(iter(running_sids)))

            session = Session(
                sid=sid,
                file_store=self.file_store,
                config=self.config,
                sio=self.sio,
                user_id=user_id,
            )
            self._local_agent_loops_by_sid[sid] = session
            asyncio.create_task(session.initialize_agent(settings))

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

        if await self.get_running_agent_loops_in_cluster(filter_to_sids={sid}):
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
                or await self.get_running_agent_loops_in_cluster(filter_to_sids={sid})
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

        await self._on_close_session(sid)
        return True

    async def close_session(self, sid: str):
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            await self._on_close_session(sid)

        redis_client = self._get_redis_client()
        if redis_client:
            await redis_client.publish(
                'oh_event',
                json.dumps({'sid': sid, 'message_type': 'close_session'}),
            )

    async def _on_close_session(self, sid: str):
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
