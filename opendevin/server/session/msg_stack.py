import atexit
import json
import os
import uuid
from typing import Dict, List

from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema.action import ActionType

CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
MSG_CACHE_FILE = os.path.join(CACHE_DIR, 'messages.json')


class Message:
    id: str = str(uuid.uuid4())
    role: str  # "user"| "assistant"
    payload: Dict[str, object]

    def __init__(self, role: str, payload: Dict[str, object]):
        self.role = role
        self.payload = payload

    def to_dict(self):
        return {'id': self.id, 'role': self.role, 'payload': self.payload}

    @classmethod
    def from_dict(cls, data: Dict):
        m = cls(data['role'], data['payload'])
        m.id = data['id']
        return m


class MessageStack:
    _messages: Dict[str, List[Message]] = {}

    def __init__(self):
        self._load_messages()
        atexit.register(self.close)

    def close(self):
        logger.info('Saving messages...')
        self._save_messages()

    def add_message(self, sid: str, role: str, message: Dict[str, object]):
        if sid not in self._messages:
            self._messages[sid] = []
        self._messages[sid].append(Message(role, message))

    def del_messages(self, sid: str):
        if sid not in self._messages:
            return
        del self._messages[sid]

    def get_messages(self, sid: str) -> List[Dict[str, object]]:
        if sid not in self._messages:
            return []
        return [msg.to_dict() for msg in self._messages[sid]]

    def get_message_total(self, sid: str) -> int:
        if sid not in self._messages:
            return 0
        cnt = 0
        for msg in self._messages[sid]:
            if 'action' in msg.payload and msg.payload['action'] in [
                ActionType.INIT,
                ActionType.RECONNECT,
                ActionType.CHANGE_TASK_STATE,
            ]:
                continue
            cnt += 1
        return cnt

    def _save_messages(self):
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        data = {}
        for sid, msgs in self._messages.items():
            data[sid] = [msg.to_dict() for msg in msgs]
        with open(MSG_CACHE_FILE, 'w+') as file:
            json.dump(data, file)

    def _load_messages(self):
        try:
            # TODO: delete useless messages
            with open(MSG_CACHE_FILE, 'r') as file:
                data = json.load(file)
                for sid, msgs in data.items():
                    self._messages[sid] = [Message.from_dict(msg) for msg in msgs]
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            pass


message_stack = MessageStack()
