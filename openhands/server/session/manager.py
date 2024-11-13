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
    sessions: dict[str, Session] = field(default_factory=dict)

    def add_or_restart_session(self, sid: str, ws_conn: WebSocket) -> Session:
        session = Session(
            sid=sid, file_store=self.file_store, ws=ws_conn, config=self.config, sio=None
        )
        self.sessions[sid] = session
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

    async def stop_session(self, sid: str) -> bool:
        session = self.sessions.pop(sid, None)
        if session:
            session.close()
        return bool(session)

    def get_existing_session(self, sid: str):
        return self.sessions.get(sid)
    
    def add_new_session(self, sio: socketio.AsyncServer | None, sid: str = None):
        session = Session(
            sid=sid, file_store=self.file_store, config=self.config, sio=sio, ws=None
        )
        self.sessions[sid] = session
        return session
    
    def alias_existing_session(self, old_sid: str, new_sid: str):
        session = self.sessions.pop(old_sid)
        if not session:
            raise RuntimeError(f'unknown_session:{old_sid}')
        self.sessions[new_sid] = session
