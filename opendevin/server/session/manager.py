import os
import json
import atexit
import signal
from typing import Callable, Any, Awaitable
from types import FrameType

from fastapi import WebSocket

from .session import Session
from .msg_stack import message_stack


CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
SESSION_CACHE_FILE = os.path.join(CACHE_DIR, 'sessions.json')


class SessionManager:
    _sessions: dict[str, Session] = {}

    def __init__(self) -> None:
        self._load_sessions()
        atexit.register(self.close)
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def add_session(self, sid: str, ws_conn: WebSocket) -> None:
        if sid not in self._sessions:
            self._sessions[sid] = Session(sid=sid, ws=ws_conn)
            return
        self._sessions[sid].update_connection(ws_conn)

    async def loop_recv(self, sid: str, dispatch: Callable[[str | None, dict[str, Any]], Awaitable[None]]) -> None:
        print(
            f'Starting loop_recv for sid: {sid}, {sid not in self._sessions}')
        """Starts listening for messages from the client."""
        if sid not in self._sessions:
            return
        await self._sessions[sid].loop_recv(dispatch)

    def close(self) -> None:
        self._save_sessions()

    def handle_signal(self, signum: int, _: FrameType | None) -> None:
        print(f'Received signal {signum}, exiting...')
        self.close()
        exit(0)

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

    def _save_sessions(self) -> None:
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

    def _load_sessions(self) -> None:
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


session_manager = SessionManager()
