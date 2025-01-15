import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from uuid import uuid4

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.server.session.conversation_manager.standalone_conversation_manager import (
    StandaloneConversationManager,
)
from openhands.utils.async_utils import wait_all
from openhands.utils.shutdown_listener import should_continue

_REDIS_POLL_TIMEOUT = 1.5
_CLEANUP_INTERVAL = 15
MAX_RUNNING_CONVERSATIONS = 3

T = TypeVar('T')


@dataclass
class _ClusterQuery(Generic[T]):
    query_id: str
    request_ids: set[str] | None
    result: T
    flag: asyncio.Event = field(default_factory=asyncio.Event)


@dataclass
class ClusteredConversationManager(StandaloneConversationManager):
    """Manages conversations in clustered mode (multiple server instances with Redis)."""

    _last_alive_timestamps: dict[str, float] = field(default_factory=dict)
    _redis_listen_task: asyncio.Task | None = field(default=None)
    _running_sid_queries: dict[str, _ClusterQuery[set[str]]] = field(
        default_factory=dict
    )
    _connection_queries: dict[str, _ClusterQuery[dict[str, str]]] = field(
        default_factory=dict
    )

    async def __aenter__(self):
        await super().__aenter__()
        self._redis_listen_task = asyncio.create_task(self._redis_subscribe())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._redis_listen_task:
            self._redis_listen_task.cancel()
            self._redis_listen_task = None
        super().__aexit__(exc_type, exc_value, traceback)

    def _get_redis_client(self):
        return getattr(self.sio.manager, 'redis', None)

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
            except Exception as e:
                try:
                    asyncio.get_running_loop()
                    logger.error(f'error_reading_from_redis:{str(e)}')
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
            sids = await self.get_running_agent_loops(
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
            connections = await self.get_connections(
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

    async def get_running_agent_loops(
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> set[str]:
        sids = await super().get_running_agent_loops(user_id, filter_to_sids)
        remote_sids = await self._get_running_agent_loops_remotely(
            user_id, filter_to_sids
        )
        return sids.union(remote_sids)

    async def _get_running_agent_loops_remotely(
        self,
        user_id: str | None = None,
        filter_to_sids: set[str] | None = None,
    ) -> set[str]:
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
        self, user_id: str | None = None, filter_to_sids: set[str] | None = None
    ) -> dict[str, str]:
        connections = await super().get_connections(user_id, filter_to_sids)
        remote_connections = await self._get_connections_remotely(
            user_id, filter_to_sids
        )
        connections.update(remote_connections)
        return connections

    async def _get_connections_remotely(
        self,
        user_id: str | None = None,
        filter_to_sids: set[str] | None = None,
    ) -> dict[str, str]:
        """Ask the rest of the cluster about connections. Wait a for a short timeout for a reply"""
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
                f'publish:_get_connections_remotely_query:{user_id}:{filter_to_sids}'
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

    async def send_to_event_stream(self, connection_id: str, data: dict):
        sid = self._local_connection_id_to_session_id.get(connection_id)
        if not sid:
            return
        session = self._local_agent_loops_by_sid.get(sid)
        if session:
            await session.dispatch(data)
        else:
            # The session is running on another node
            redis_client = self._get_redis_client()
            if redis_client:
                await redis_client.publish(
                    'session_msg',
                    json.dumps({'message_type': 'event', 'sid': sid, 'data': data}),
                )

    async def close_session(self, sid: str):
        redis_client = self._get_redis_client()
        if redis_client:
            await redis_client.publish(
                'session_msg',
                json.dumps({'message_type': 'close_session', 'sid': sid}),
            )
        await self._close_session(sid)

    async def _cleanup_stale(self):
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
                    f'Local connections: {len(self._local_connection_id_to_session_id)}'
                )
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

    async def _close_session(self, sid: str):
        session = self._local_agent_loops_by_sid.pop(sid, None)
        if session:
            await session.close()
            redis_client = self._get_redis_client()
            if redis_client:
                await redis_client.publish(
                    'session_msg',
                    json.dumps({'message_type': 'session_closing', 'sid': sid}),
                )
            # Create a list of items to process to avoid modifying dict during iteration
            items = list(self._local_connection_id_to_session_id.items())
            for connection_id, local_sid in items:
                if sid == local_sid:
                    await self.sio.disconnect(connection_id)
