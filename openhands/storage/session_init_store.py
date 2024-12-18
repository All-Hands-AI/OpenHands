from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from openhands.core.config.app_config import AppConfig
from openhands.server.session.session_init_data import SessionInitData
from openhands.storage import get_file_store
from openhands.storage.files import FileStore


class SessionInitStore(ABC):
    """
    Storage for SessionInitData. May or may not support multiple users depending on the environment
    """

    @abstractmethod
    def load(self) -> SessionInitData | None:
        """Load session init data"""

    @abstractmethod
    def store(self, session_init_data: SessionInitData):
        """Store session init data"""

    @classmethod
    @abstractmethod
    def get_instance(cls, config: AppConfig, token: str | None) -> SessionInitStore:
        """Get a store for the user represented by the token given"""


@dataclass
class FileSessionInitStore(SessionInitStore):
    file_store: FileStore
    path: str = 'config.json'

    def load(self) -> SessionInitData | None:
        try:
            json_str = self.file_store.read(self.path)
            kwargs = json.loads(json_str)
            item = SessionInitData(**kwargs)
            return item
        except FileNotFoundError:
            return None

    def store(self, item: SessionInitData):
        json_str = json.dumps(item.__dict__)
        self.file_store.write(self.path, json_str)

    @classmethod
    def get_instance(cls, config: AppConfig, token: str | None):
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileSessionInitStore(file_store)
