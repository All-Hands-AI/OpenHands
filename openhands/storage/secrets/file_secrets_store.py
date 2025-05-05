from __future__ import annotations

import json
from dataclasses import dataclass

from openhands.core.config.app_config import AppConfig
from openhands.storage import get_file_store
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.files import FileStore
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.utils.async_utils import call_sync_from_async


@dataclass
class FileSecretsStore(SecretsStore):
    file_store: FileStore
    path: str = 'secrets.json'

    async def load(self) -> UserSecrets | None:
        try:
            json_str = await call_sync_from_async(self.file_store.read, self.path)
            kwargs = json.loads(json_str)
            secrets = UserSecrets(**kwargs)
            return secrets
        except FileNotFoundError:
            return None

    async def store(self, secrets: UserSecrets) -> None:
        json_str = secrets.model_dump_json(context={'expose_secrets': True})
        await call_sync_from_async(self.file_store.write, self.path, json_str)

    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> FileSecretsStore:
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileSecretsStore(file_store)
