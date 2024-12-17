import json
from dataclasses import dataclass, field
from typing import Type

from openhands.server import shared
from openhands.server.auth import AuthError, decrypt_str, encrypt_str
from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import file_store
from openhands.storage.files import FileStore
from openhands.storage.item_store import ItemStore, T


@dataclass
class FileItemStore(ItemStore[T]):
    type: Type = SessionInitData
    files: FileStore = file_store
    pattern: str = 'users/github/{id}/config.json'
    jwt_secret: str = field(default_factory=lambda: shared.config.jwt_secret)

    def load(self, id: str) -> T | None:
        file_name = self.pattern.format(id=id)
        try:
            json_str = self.files.read(file_name)
            kwargs = json.loads(json_str)
            for key, value in kwargs.items():
                if self.should_encrypt(key):
                    try:
                        value = decrypt_str(value, self.jwt_secret)
                    except AuthError:
                        value = None
                    kwargs[key] = value
            item = self.type(**kwargs)
            return item
        except FileNotFoundError:
            return None

    def store(self, id: str, item: T):
        kwargs = {}
        for key, value in item.__dict__.items():
            if self.should_encrypt(key):
                value = encrypt_str(value, self.jwt_secret)
            kwargs[key] = value
        json_str = json.dumps(kwargs)
        file_name = self.pattern.format(id=id)
        self.files.write(file_name, json_str)

    def should_encrypt(self, key: str):
        return 'key' in key or 'token' in key
