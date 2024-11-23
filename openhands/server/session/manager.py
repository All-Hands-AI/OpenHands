import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Callable

import socketio

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStream, session_exists
from openhands.runtime.base import RuntimeUnavailableError
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import ROOM_KEY, Session
from openhands.storage.files import FileStore
from openhands.utils.async_utils import wait_all
from openhands.utils.shutdown_listener import should_continue

_CONNECTION_KEY = "oh_session:{sid}"
_SESSION_RUNNING_TIMEOUT = 1.5


@dataclass
class SessionManager:
    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore
    local_sessions_by_sid: dict[str, Session] = field(default_factory=dict)
    local_connection_id_to_session_id: dict[str, str] = field(default_factory=dict)
    _redis_listen_task: asyncio.Task | None = None
    _session_is_running_flags: dict[str, asyncio.Event] = field(default_factory=dict)

    async def __aenter__(self):
        redis_client = self._get_redis_client()
        if redis_client:
            self._redis_listen_task = asyncio.create_task(self._redis_subscribe())
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._redis_listen_task:
            self._redis_listen_task.cancel()
            self._redis_listen_task = None

    def _get_redis_client(self):
        redis_client = getattr(self.sio.manager, "redis", None)
        return redis_client
    
    async def _redis_subscribe(self):
        """
        We use a redis backchannel to send actions between server nodes
        """
        redis_client = self._get_redis_client()
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("oh_event")
        while should_continue():
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=5)
                if message:
                    data = json.loads(message['data'])
                    logger.info(f"got_published_message:{message}")
                    sid = data["sid"]
                    message_type = data["message_type"]
                    if message_type == "event":
                        session = self.local_sessions_by_sid.get(sid)
                        if session:
                            await session.dispatch(data["data"])
                    elif message_type == "is_session_running":
                        # Another node in the cluster is asking if the current node is running the session given.
                        session = self.local_sessions_by_sid.get(sid)
                        if session:
                            await redis_client.publish("oh_event", json.dumps({
                                "sid": sid,
                                "message_type": "session_is_running"
                            }))
                    elif message_type == "session_is_running":
                        flag = self._session_is_running_flags.get(sid)
                        if flag:
                            flag.set()
                    elif message_type == "session_closing":
                        logger.info(f"session_closing:{sid}")
                        for connection_id, local_sid in self.local_connection_id_to_session_id.items():
                            if sid == local_sid:
                                logger.warning('local_connection_to_closing_session')


            except asyncio.CancelledError:
                return
            except:
                logger.warning("error_reading_from_redis", exc_info=True, stack_info=True)

    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        start_time = time.time()
        if not await session_exists(sid, self.file_store):
            return None
        c = Conversation(sid, file_store=self.file_store, config=self.config)
        try:
            await c.connect()
        except RuntimeUnavailableError as e:
            logger.error(f'Error connecting to conversation {c.sid}: {e}')
            return None
        end_time = time.time()
        logger.info(
            f'Conversation {c.sid} connected in {end_time - start_time} seconds'
        )
        return c

    async def detach_from_conversation(self, conversation: Conversation):
        await conversation.disconnect()

    async def init_or_join_session(self, sid: str, connection_id: str, data: dict):
        await self.sio.enter_room(connection_id, ROOM_KEY.format(sid=sid))
        self.local_connection_id_to_session_id[connection_id] = sid
        
        # If we have a local session running, use that
        session = self.local_sessions_by_sid.get(sid)
        if session:
            logger.info(f'found_local_session:{sid}')
            return session.agent_session.event_stream        

        # If there is a remote session running, retrieve existing events for that
        redis_client = self._get_redis_client()
        if redis_client and await self._is_session_running_in_cluster(sid):
                return EventStream(sid, self.file_store)
        
        return await self.start_local_session(sid, data)

    async def _is_session_running_in_cluster(self, sid: str) -> bool:
        """ As the rest of the cluster if a session is running. Wait a for a short timeout for a reply """
        # Create a flag for the callback
        flag = asyncio.Event()
        self._session_is_running_flags[sid] = flag
        try:
            await self._get_redis_client().publish("oh_event", json.dumps({
                "sid": sid,
                "message_type": "is_session_running",
            }))
            async with asyncio.timeout(_SESSION_RUNNING_TIMEOUT):
                await flag.wait()

            result = flag.is_set()
            return result
        except TimeoutError:
            # Nobody replied in time
            return False
        finally:
            self._session_is_running_flags.pop(sid)

    async def start_local_session(self, sid: str, data: dict):

        # Start a new local session
        logger.info(f'start_new_local_session:{sid}')
        session = Session(
            sid=sid, file_store=self.file_store, config=self.config, sio=self.sio
        )
        self.local_sessions_by_sid[sid] = session
        await session.initialize_agent(data)
        return session.agent_session.event_stream
    
    
    async def send_to_event_stream(self, connection_id: str, data: dict):
        # If there is a local session running, send to that
        sid = self.local_connection_id_to_session_id.get(connection_id)
        if sid:
            session = self.local_sessions_by_sid.get(sid)
            if session:
                await session.dispatch(data)
                return
        
        # If there is a remote session running, send to that
        redis_client = self._get_redis_client()
        if redis_client:
            await redis_client.publish("oh_event", json.dumps({
                "sid": sid,
                "message_type": "event",
                "data": data,
            }))
            return
        
        raise RuntimeError(f'no_connected_session:{sid}')
    
    async def disconnect_from_session(self, connection_id: str):
        sid = self.local_connection_id_to_session_id.pop(connection_id, None)
        if not sid:
            # This can occur if the init action was never run.
            logger.warning(f'disconnect_from_uninitialized_session:{connection_id}')
            return

        session = self.local_sessions_by_sid.get(sid)
        if session:
            logger.info(f'close_session:{connection_id}:{sid}')
            if should_continue():
                asyncio.create_task(self._cleanup_session_later(session, connection_id))
            else:
                await self._cleanup_session(session, connection_id, True)
            
    async def _cleanup_session_later(self, session: Session, connection_id: str):
        # Once there have been no connections to a session for a reasonable period, we close it
        try:
            await asyncio.sleep(self.config.sandbox.close_delay)
        finally:
            # If the sleep was cancelled, we still want to close these
            await self._cleanup_session(session, connection_id, False)
    
    async def _cleanup_session(self, session: Session, connection_id: str, force: bool):
            # Get local connections
            has_local_connections = next((
                True for v in self.local_connection_id_to_session_id.values()
                if v == session.sid
            ), False)

            # If no local connections, get connections through redis
            redis_connections = None
            redis_client = self._get_redis_client()
            if redis_client:
                key = _CONNECTION_KEY.format(sid=session.sid)
                await redis_client.lrem(key, 0, connection_id)
                redis_connections = await redis_client.lrange(key, 0, -1)
                redis_connections = [
                    c.decode() for c in redis_connections
                ]
                logger.info(f'close_orphaned_session:{redis_connections}')
                if not redis_connections:
                    await redis_client.delete(key)
                redis_connections = [
                    c for c in redis_connections
                    if c not in self.local_connection_id_to_session_id
                ]
                logger.info(f'close_orphaned_session:2:{redis_connections}')

            # If no connections, close session
            if force or (not has_local_connections and not redis_connections):

                # We alert the cluster in case they are interested
                if redis_client:
                    await redis_client.publish("oh_event", json.dumps({
                        "sid": session.sid,
                        "message_type": "session_closing"
                    }))

                logger.info(f'do_close_session')
                session.close()
                self.local_sessions_by_sid.pop(session.sid, None)
