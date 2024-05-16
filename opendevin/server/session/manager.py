import asyncio
import time

from fastapi import WebSocket

from opendevin.core.logger import opendevin_logger as logger

from .session import Session


class SessionManager:
    _sessions: dict[str, Session] = {}
    cleanup_interval: int = 300
    session_timeout: int = 600

    def __init__(self):
        asyncio.create_task(self._cleanup_sessions())

    def add_or_restart_session(self, sid: str, ws_conn: WebSocket) -> Session:
        if sid in self._sessions:
            asyncio.create_task(self._sessions[sid].close())
        self._sessions[sid] = Session(sid=sid, ws=ws_conn)
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
        while True:
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
                del self._sessions[sid]
                logger.info(f'Session {sid} has been removed due to inactivity.')

            await asyncio.sleep(self.cleanup_interval)
