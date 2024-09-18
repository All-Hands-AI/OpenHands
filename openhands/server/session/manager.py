import asyncio
import time

from fastapi import WebSocket

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.utils.shutdown_listener import should_continue
from openhands.server.session.session import Session
from openhands.storage.files import FileStore


class SessionManager:
    _sessions: dict[str, Session] = {}
    cleanup_interval: int = 300
    session_timeout: int = 600

    def __init__(self, config: AppConfig, file_store: FileStore):
        asyncio.create_task(self._cleanup_sessions())
        self.config = config
        self.file_store = file_store

    def add_or_restart_session(self, sid: str, ws_conn: WebSocket) -> Session:
        if sid in self._sessions:
            asyncio.create_task(self._sessions[sid].close())
        self._sessions[sid] = Session(
            sid=sid, file_store=self.file_store, ws=ws_conn, config=self.config
        )
        return self._sessions[sid]

    def get_session(self, sid: str) -> Session | None:
        if sid not in self._sessions:
            return None
        return self._sessions.get(sid)

    async def send(self, sid: str, data: dict[str, object]) -> bool:
        """Sends data to the client."""
        if sid not in self._sessions:
            return False
        return await self._sessions[sid].send(data)

    async def send_error(self, sid: str, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send(sid, {'error': True, 'message': message})

    async def send_message(self, sid: str, message: str) -> bool:
        """Sends a message to the client."""
        return await self.send(sid, {'message': message})

    async def _cleanup_sessions(self):
        while should_continue():
            current_time = time.time()
            session_ids_to_remove = []
            for sid, session in list(self._sessions.items()):
                # if session inactive for a long time, remove it
                if (
                    not session.is_alive
                    and current_time - session.last_active_ts > self.session_timeout
                ):
                    session_ids_to_remove.append(sid)

            for sid in session_ids_to_remove:
                to_del_session: Session | None = self._sessions.pop(sid, None)
                if to_del_session is not None:
                    await to_del_session.close()
                    logger.info(
                        f'Session {sid} and related resource have been removed due to inactivity.'
                    )

            await asyncio.sleep(self.cleanup_interval)
