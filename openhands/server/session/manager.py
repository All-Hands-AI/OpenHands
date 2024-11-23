import asyncio
import json
import time
from dataclasses import dataclass, field

import socketio

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import EventStream, session_exists
from openhands.runtime.base import RuntimeUnavailableError
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import ROOM_KEY, Session
from openhands.storage.files import FileStore
from openhands.utils.shutdown_listener import should_continue

_CONNECTION_KEY = "oh_session:{sid}"


@dataclass
class SessionManager:
    sio: socketio.AsyncServer
    config: AppConfig
    file_store: FileStore
    local_sessions_by_sid: dict[str, Session] = field(default_factory=dict)
    local_connection_id_to_session_id: dict[str, str] = field(default_factory=dict)
    _redis_listen_task: asyncio.Task | None = None

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
                    sid = data["sid"]
                    message_type = data["message_type"]
                    if message_type == "event":
                        session = self.local_sessions_by_sid.get(sid)
                        if session:
                            await session.dispatch(data["data"])
                    elif message_type == "restart":
                        logger.info("got_transfer_request")
                        connection_id = data["connection_id"]
                        if self.local_connection_id_to_session_id.get(connection_id) == sid:
                            logger.info("transferring_session_to_local")
                            await self.init_or_join_session(sid, connection_id, data["settings"])
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

        # If there is a remote session running, mark a connection to that
        redis_client = self._get_redis_client()
        if redis_client:
            num_connections = await redis_client.rpush(_CONNECTION_KEY.format(sid=sid), connection_id)
            logger.info(f'num_redis_connections:{sid}:{num_connections}')
            # More than one remote connection implies session is already running remotely...
            if num_connections != 1:
                logger.info(f'session_running_elsewhere_in_cluster:{sid}')
                event_stream = EventStream(sid, self.file_store)
                return event_stream

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

            if force and redis_connections:
                logger.info(f'transferring_session')
                await redis_client.publish("oh_event", json.dumps({
                    "sid": session.sid,
                    "message_type": "restart",
                    "connection_id": redis_connections[0],
                    "settings": session.settings,
                }))

            # If no connections, close session
            if force or (not has_local_connections and not redis_connections):
                logger.info(f'do_close_session')
                session.close()
                self.local_sessions_by_sid.pop(session.sid, None)
