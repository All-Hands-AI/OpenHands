from dataclasses import dataclass

from fastapi import WebSocket

from openhands.core.config import AppConfig
from openhands.events.stream import session_exists
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import Session
from openhands.storage.files import FileStore


@dataclass
class SessionManager:
    config: AppConfig
    file_store: FileStore
    session_timeout: int = 600

    def add_or_restart_session(self, sid: str, ws_conn: WebSocket) -> Session:
        return Session(
            sid=sid, file_store=self.file_store, ws=ws_conn, config=self.config
        )

    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        if not await session_exists(sid, self.file_store):
            return None
        c = Conversation(sid, file_store=self.file_store, config=self.config)
        await c.connect()
        return c

    async def detach_from_conversation(self, conversation: Conversation):
        await conversation.disconnect()
