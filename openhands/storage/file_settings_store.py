from __future__ import annotations

import json
from dataclasses import dataclass

from openhands.core.config.app_config import AppConfig
from openhands.server.settings import Settings
from openhands.storage import get_file_store
from openhands.storage.files import FileStore
from openhands.storage.settings_store import SettingsStore


@dataclass
class FileSettingsStore(SettingsStore):
    file_store: FileStore
    path: str = 'config.json'

    async def load(self) -> Settings | None:
        try:
            json_str = self.file_store.read(self.path)
            kwargs = json.loads(json_str)
            settings = Settings(**kwargs)
            return settings
        except FileNotFoundError:
            return None

    async def store(self, settings: Settings):
        json_str = json.dumps(settings.__dict__)
        self.file_store.write(self.path, json_str)

    @classmethod
    async def get_instance(cls, config: AppConfig, token: str | None):
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileSettingsStore(file_store)
