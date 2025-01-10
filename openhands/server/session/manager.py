import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Generic, Iterable, TypeVar
from uuid import uuid4

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

_REDIS_POLL_TIMEOUT = 1.5
_CHECK_ALIVE_INTERVAL = 15

_CLEANUP_INTERVAL = 15
_CLEANUP_EXCEPTION_WAIT_TIME = 15
MAX_RUNNING_CONVERSATIONS = 3
T = TypeVar('T')


class ConversationDoesNotExistError(Exception):
    pass


@dataclass
class _ClusterQuery(Generic[T]):
    query_id: str
    request_ids: set[str] | None
    result: T
    flag: asyncio.Event = field(default_factory=asyncio.Event)


@dataclass
class SessionManager:
    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore
    _local_agent_loops_by_sid: dict[str, Session] = field(default_factory=dict)
    _local_connection_id_to_session_id: dict[str, str] = field(default_factory=dict)
    _last_alive_timestamps: dict[str, float] = field(default_factory=dict)
    _redis_listen_task: asyncio.Task | None = None
    _running_sid_queries: dict[str, _ClusterQuery[set[str]]] = field(
        default_factory=dict
    )
    _active_conversations: dict[str, tuple[Conversation, int]] = field(
        default_factory=dict
    )
    _conversations_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _cleanup_task: asyncio.Task | None = None
    _connection_queries: dict[str, _ClusterQuery[dict[str, str]]] = field(
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
        await pubsub.subscribe('session_msg')
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
            query_id = data['query_id']
            sids = self._get_running_agent_loops_locally(
                data.get('user_id'), data.get('filter_to_sids')
            )
            if sids:
                await self._get_redis_client().publish(
                    'session_msg',
                    json.dumps(
                        {
                            'query_id': query_id,
                            'sids': list(sids),
                            'message_type': 'running_agent_loops_response',
                        }
                    ),
                )
        elif message_type == 'running_agent_loops_response':
            query_id = data['query_id']
            for sid in data['sids']:
                self._last_alive_timestamps[sid] = time.time()
            running_query = self._running_sid_queries.get(query_id)
            if running_query:
                running_query.result.update(data['sids'])
                if running_query.request_ids is not None and len(
                    running_query.request_ids
                ) == len(running_query.result):
                    running_query.flag.set()
        elif message_type == 'connections_query':
            # Another node in the cluster is asking if the current node is connected to a session
            query_id = data['query_id']
            connections = self._get_connections_locally(
                data.get('user_id'), data.get('filter_to_sids')
            )
            if connections:
                await self._get_redis_client().publish(
                    'session_msg',
                    json.dumps(
                        {
                            'query_id': query_id,
                            'connections': connections,
                            'message_type': 'connections_response',
                        }
                    ),
                )
        elif message_type == 'connections_response':
            query_id = data['query_id']
            connection_query = self._connection_queries.get(query_id)
            if connection_query:
                connection_query.result.update(**data['connections'])
                if connection_query.request_ids is not None and len(
                    connection_query.request_ids
                ) == len(connection_query.result):
                    connection_query.flag.set()
        elif message_type == 'close_session':
            sid = data['sid']
            if sid in self._local_agent_loops_by_sid:
                await self._close_session(sid)
        elif message_type == 'session_closing':
            # Session closing event - We only get this in the event of graceful shutdown,
            # which can't be guaranteed - nodes can simply vanish unexpectedly!
            sid = data['sid']
            logger.debug(f'session_closing:{sid}')
            # Create a list of items to process to avoid modifying dict during iteration
            items = list(self._local_connection_id_to_session_id.items())
            for connection_id, local_sid in items:
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
        self, sid: str, connection_id: str, settings: Settings, user_id: int | None
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

    async def _cleanup_stale(self):
        while should_continue():
            if self._get_redis_client():
                # Debug info for HA envs
                logger.info(
                    f'Running agent loops: {len(self._local_agent_loops_by_sid)}'
                )
                logger.info(
                    f'Local connections: {len(self._local_connection_id_to_session_id)}'
                )
            try:
                close_threshold = time.time() - self.config.sandbox.close_delay
                running_loops = list(self._local_agent_loops_by_sid.items())
                running_loops.sort(key=lambda item: item[1].last_active_ts)
                sid_to_close: list[str] = []
                for sid, session in running_loops:
                    controller = session.agent_session.controller
                    state = controller.state if controller else AgentState.STOPPED
                    if (
                        session.last_active_ts < close_threshold
                        and state != AgentState.RUNNING
                    ):
                        sid_to_close.append(sid)

                connections = self._get_connections_locally(
                    filter_to_sids=set(sid_to_close)
                )
                connected_sids = {sid for _, sid in connections.items()}
                sid_to_close = [
                    sid for sid in sid_to_close if sid not in connected_sids
                ]

                if sid_to_close:
                    connections = await self._get_connections_remotely(
                        filter_to_sids=set(sid_to_close)
                    )
                    connected_sids = {sid for _, sid in connections.items()}
                    sid_to_close = [
                        sid for sid in sid_to_close if sid not in connected_sids
                    ]

                await wait_all(self._close_session(sid) for sid in sid_to_close)
                await asyncio.sleep(_CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                await wait_all(
                    self._close_session(sid) for sid in self._local_agent_loops_by_sid
                )
                return
            except Exception:
                logger.warning('error_cleaning_stale', exc_info=True)
                await asyncio.sleep(_CLEANUP_EXCEPTION_WAIT_TIME)

    async def is_agent_loop_running(self, sid: str) -> bool:
        sids = await self.get_running_agent_loops(filter_to_sids={sid})
        return bool(sids)

    async def get_running_agent_loops(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        """Get the running session ids. If a user is supplied, then the results are limited to session ids for that user. If a set of filter_to_sids is supplied, then results are limited to these ids of interest."""
        sids = self._get_running_agent_loops_locally(user_id, filter_to_sids)
        remote_sids = await self._get_running_agent_loops_remotely(
            user_id, filter_to_sids
        )
        return sids.union(remote_sids)

    def _get_running_agent_loops_locally(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        items: Iterable[tuple[str, Session]] = self._local_agent_loops_by_sid.items()
        if filter_to_sids is not None:
            items = (item for item in items if item[0] in filter_to_sids)
        if user_id:
            items = (item for item in items if item[1].user_id == user_id)
        sids = {sid for sid, _ in items}
        return sids

    async def _get_running_agent_loops_remotely(
        self,
        user_id: int | None = None,
        filter_to_sids: set[str] | None = None,
    ) -> set[str]:
        """As the rest of the cluster if a session is running. Wait a for a short timeout for a reply"""
        redis_client = self._get_redis_client()
        if not redis_client:
            return set()

        flag = asyncio.Event()
        query_id = str(uuid4())
        query = _ClusterQuery[set[str]](
            query_id=query_id, request_ids=filter_to_sids, result=set()
        )
        self._running_sid_queries[query_id] = query
        try:
            logger.debug(
                f'publish:_get_running_agent_loops_remotely_query:{user_id}:{filter_to_sids}'
            )
            data: dict = {
                'query_id': query_id,
                'message_type': 'running_agent_loops_query',
            }
            if user_id:
                data['user_id'] = user_id
            if filter_to_sids:
                data['filter_to_sids'] = list(filter_to_sids)
            await redis_client.publish('session_msg', json.dumps(data))
            async with asyncio.timeout(_REDIS_POLL_TIMEOUT):
                await flag.wait()

            return query.result
        except TimeoutError:
            # Nobody replied in time
            return query.result
        finally:
            self._running_sid_queries.pop(query_id, None)

    async def get_connections(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        connection_ids = self._get_connections_locally(user_id, filter_to_sids)
        remote_connection_ids = await self._get_connections_remotely(
            user_id, filter_to_sids
        )
        connection_ids.update(**remote_connection_ids)
        return connection_ids

    def _get_connections_locally(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
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

    async def _get_connections_remotely(
        self, user_id: int | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        redis_client = self._get_redis_client()
        if not redis_client:
            return {}

        flag = asyncio.Event()
        query_id = str(uuid4())
        query = _ClusterQuery[dict[str, str]](
            query_id=query_id, request_ids=filter_to_sids, result={}
        )
        self._connection_queries[query_id] = query
        try:
            logger.debug(
                f'publish:get_connections_remotely_query:{user_id}:{filter_to_sids}'
            )
            data: dict = {
                'query_id': query_id,
                'message_type': 'connections_query',
            }
            if user_id:
                data['user_id'] = user_id
            if filter_to_sids:
                data['filter_to_sids'] = list(filter_to_sids)
            await redis_client.publish('session_msg', json.dumps(data))
            async with asyncio.timeout(_REDIS_POLL_TIMEOUT):
                await flag.wait()

            return query.result
        except TimeoutError:
            # Nobody replied in time
            return query.result
        finally:
            self._connection_queries.pop(query_id, None)

    async def maybe_start_agent_loop(
        self, sid: str, settings: Settings, user_id: int | None = None
    ) -> EventStream:
        logger.info(f'maybe_start_agent_loop:{sid}')
        session: Session | None = None
        if not await self.is_agent_loop_running(sid):
            logger.info(f'start_agent_loop:{sid}')

            response_ids = await self.get_running_agent_loops(user_id)
            if len(response_ids) >= MAX_RUNNING_CONVERSATIONS:
                logger.info('too_many_sessions_for:{user_id}')
                await self.close_session(next(iter(response_ids)))

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

        if await self._get_running_agent_loops_remotely(filter_to_sids={sid}):
            logger.info(f'found_remote_agent_loop:{sid}')
            return EventStream(sid, self.file_store)

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

        redis_client = self._get_redis_client()
        if redis_client:
            # If we have a recent report that the session is alive in another pod
            last_alive_at = self._last_alive_timestamps.get(sid) or 0
            next_alive_check = last_alive_at + _CHECK_ALIVE_INTERVAL
            if (
                next_alive_check > time.time()
                or await self._get_running_agent_loops_remotely(filter_to_sids={sid})
            ):
                # Send the event to the other pod
                await redis_client.publish(
                    'session_msg',
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

        redis_client = self._get_redis_client()
        if redis_client:
            await redis_client.publish(
                'session_msg',
                json.dumps({'sid': sid, 'message_type': 'close_session'}),
            )

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
        # We alert the cluster in case they are interested
        try:
            redis_client = self._get_redis_client()
            if redis_client:
                await redis_client.publish(
                    'session_msg',
                    json.dumps({'sid': session.sid, 'message_type': 'session_closing'}),
                )
        except Exception:
            logger.info(
                'error_publishing_close_session_event', exc_info=True, stack_info=True
            )

        await session.close()
        logger.info(f'closed_session:{session.sid}')
