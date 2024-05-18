import asyncio
import atexit
import json
import os
import time
from typing import Callable

from fastapi import WebSocket

from opendevin.core.logger import opendevin_logger as logger

from .msg_stack import message_stack
from .session import Session

CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
SESSION_CACHE_FILE = os.path.join(CACHE_DIR, 'sessions.json')


class SessionManager:
    _sessions: dict[str, Session] = {}
    cleanup_interval: int = 300
    session_timeout: int = 600

    def __init__(self):
        self._load_sessions()
        atexit.register(self.close)
        asyncio.create_task(self._cleanup_sessions())

    def add_session(self, sid: str, ws_conn: WebSocket):
        if sid not in self._sessions:
            self._sessions[sid] = Session(sid=sid, ws=ws_conn)
            return
        self._sessions[sid].update_connection(ws_conn)

    async def loop_recv(self, sid: str, dispatch: Callable):
        print(f'Starting loop_recv for sid: {sid}')
        """Starts listening for messages from the client."""
        if sid not in self._sessions:
            return
        await self._sessions[sid].loop_recv(dispatch)

    def close(self):
        logger.info('Saving sessions...')
        self._save_sessions()

    async def send(self, sid: str, data: dict[str, object]) -> bool:
        """Sends data to the client."""
        message_stack.add_message(sid, 'assistant', data)
        if sid not in self._sessions:
            return False
        return await self._sessions[sid].send(data)

    async def send_error(self, sid: str, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send(sid, {'error': True, 'message': message})

    async def send_message(self, sid: str, message: str) -> bool:
        """Sends a message to the client."""
        return await self.send(sid, {'message': message})

    def _save_sessions(self):
        data = {}
        for sid, conn in self._sessions.items():
            data[sid] = {
                'sid': conn.sid,
                'last_active_ts': conn.last_active_ts,
                'is_alive': conn.is_alive,
            }
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        with open(SESSION_CACHE_FILE, 'w+') as file:
            json.dump(data, file)

    def _load_sessions(self):
        try:
            with open(SESSION_CACHE_FILE, 'r') as file:
                data = json.load(file)
                for sid, sdata in data.items():
                    conn = Session(sid, None)
                    ok = conn.load_from_data(sdata)
                    if ok:
                        self._sessions[sid] = conn
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            pass

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
