import os
import json
import atexit
import signal
import uuid

from opendevin.schema.action import ActionType
from opendevin.logging import opendevin_logger as logger
from typing import Any
from types import FrameType


CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
MSG_CACHE_FILE = os.path.join(CACHE_DIR, 'messages.json')


class Message:
    id: str = str(uuid.uuid4())
    role: str  # "user"| "assistant"
    payload: dict[str, object]

    def __init__(self, role: str, payload: dict[str, object]) -> None:
        self.role = role
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return {'id': self.id, 'role': self.role, 'payload': self.payload}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Message':
        m = cls(data['role'], data['payload'])
        m.id = data['id']
        return m


class MessageStack:
    _messages: dict[str, list[Message]] = {}

    def __init__(self) -> None:
        self._load_messages()
        atexit.register(self.close)
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def close(self) -> None:
        self._save_messages()

    def handle_signal(self, signum: int, _: FrameType | None) -> None:
        logger.info(f'Received signal {signum}, exiting...')
        self.close()
        exit(0)

    def add_message(self, sid: str, role: str, message: dict[str, object]) -> None:
        if sid not in self._messages:
            self._messages[sid] = []
        self._messages[sid].append(Message(role, message))

    def del_messages(self, sid: str) -> None:
        if sid not in self._messages:
            return
        del self._messages[sid]

    def get_messages(self, sid: str) -> list[dict[str, object]]:
        if sid not in self._messages:
            return []
        return [msg.to_dict() for msg in self._messages[sid]]

    def get_message_total(self, sid: str) -> int:
        if sid not in self._messages:
            return 0
        cnt = 0
        for msg in self._messages[sid]:
            # Ignore assistant init message for now.
            if 'action' in msg.payload and msg.payload['action'] == ActionType.INIT:
                continue
            cnt += 1
        return cnt

    def _save_messages(self) -> None:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        data = {}
        for sid, msgs in self._messages.items():
            data[sid] = [msg.to_dict() for msg in msgs]
        with open(MSG_CACHE_FILE, 'w+') as file:
            json.dump(data, file)

    def _load_messages(self) -> None:
        try:
            # TODO: delete useless messages
            with open(MSG_CACHE_FILE, 'r') as file:
                data = json.load(file)
                for sid, msgs in data.items():
                    self._messages[sid] = [
                        Message.from_dict(msg) for msg in msgs]
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            pass


message_stack = MessageStack()
