import time
from dataclasses import dataclass, field

from fastapi import WebSocket
import socketio

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import session_exists
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import Session
from openhands.storage.files import FileStore


@dataclass
class SessionManager:
    config: AppConfig
    file_store: FileStore
    local_sessions_by_sid: dict[str, Session] = field(default_factory=dict)
    local_sessions_by_connection_id: dict[str, Session] = field(default_factory=dict)

    # TODO: Delete me!
    def add_or_restart_session(self, sid: str, ws_conn: WebSocket) -> Session:
        session = Session(
            sid=sid, file_store=self.file_store, ws=ws_conn, config=self.config, sio=None
        )
        return session

    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        start_time = time.time()
        if not await session_exists(sid, self.file_store):
            return None
        c = Conversation(sid, file_store=self.file_store, config=self.config)
        await c.connect()
        end_time = time.time()
        logger.info(
            f'Conversation {c.sid} connected in {end_time - start_time} seconds'
        )
        return c

    async def detach_from_conversation(self, conversation: Conversation):
        await conversation.disconnect()

    # TODO: Delete me!
    async def stop_session(self, sid: str) -> bool:
        session = self.sessions.pop(sid, None)
        if session:
            session.close()
        return bool(session)

    async def init_or_join_local_session(self, sio: socketio.AsyncServer, sid: str, connection_id: str, data: dict):
        """ If there is no local session running, initialize one """
        if sid not in self.local_sessions_by_sid:
            session = Session(
                sid=sid, file_store=self.file_store, config=self.config, sio=sio, ws=None
            )
            session.connect(connection_id)
            self.local_sessions_by_sid[sid] = session
            self.local_sessions_by_connection_id[connection_id] = session
            await session.initialize_agent(data)
        else:
            session.connect(connection_id)
            self.local_sessions_by_connection_id[connection_id] = session
        return session
    
    def get_local_session(self, connection_id: str) -> Session:
        return self.local_sessions_by_connection_id[connection_id]
    
    def disconnect_from_local_session(self, connection_id: str):
        session = self.local_sessions_by_connection_id.pop(connection_id, None)
        if not session:
            # This can occur if the init action was never run.
            logger.warning(f'disconnect_from_uninitialized_session:{connection_id}')
            return
        if session.disconnect(connection_id):
            self.local_sessions_by_sid.pop(session.sid)
