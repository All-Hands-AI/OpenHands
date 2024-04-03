import time
from typing import Dict, Callable
from fastapi import WebSocket, WebSocketDisconnect
from .msg_stack import message_stack

DEL_DELT_SEC = 60 * 60 * 5


class Session:
    sid: str
    websocket: WebSocket | None
    last_active_ts: int = 0
    is_alive: bool = True

    def __init__(self, sid: str, ws: WebSocket | None):
        self.sid = sid
        self.websocket = ws
        self.last_active_ts = int(time.time())

    async def loop_recv(self, dispatch: Callable):
        try:
            if self.websocket is None:
                return
            while True:
                try:
                    data = await self.websocket.receive_json()
                except ValueError:
                    await self.send_error("Invalid JSON")
                    continue

                message_stack.add_message(self.sid, "user", data)
                action = data.get("action", None)
                await dispatch(action, data)
        except WebSocketDisconnect:
            self.is_alive = False
            print(f"WebSocket disconnected, sid: {self.sid}")
        except RuntimeError as e:
            # WebSocket is not connected
            if "WebSocket is not connected" in str(e):
                self.is_alive = False
            print(f"Error in loop_recv: {e}")

    async def send(self, data: Dict[str, object]) -> bool:
        try:
            if self.websocket is None or not self.is_alive:
                return False
            await self.websocket.send_json(data)
            self.last_active_ts = int(time.time())
            return True
        except WebSocketDisconnect:
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send({"error": True, "message": message})

    async def send_message(self, message: str) -> bool:
        """Sends a message to the client."""
        return await self.send({"message": message})

    def update_connection(self, ws: WebSocket):
        self.websocket = ws
        self.is_alive = True
        self.last_active_ts = int(time.time())

    def load_from_data(self, data: Dict) -> bool:
        self.last_active_ts = data.get("last_active_ts", 0)
        if self.last_active_ts < int(time.time()) - DEL_DELT_SEC:
            return False
        self.is_alive = data.get("is_alive", False)
        return True
