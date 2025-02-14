from __future__ import annotations

import hashlib

from abc import abstractmethod
from base64 import b64decode, b64encode
from cryptography.fernet import Fernet
from dataclasses import dataclass

from pydantic import SecretStr

from openhands.core.config.app_config import AppConfig
from openhands.storage import get_file_store
from openhands.storage.data_models.user_secret import UserSecret
from openhands.storage.data_models.user_secret_result_set import UserSecretResultSet
from openhands.storage.files import FileStore
from openhands.storage.user_secrets.user_secret_store import UserSecretStore


@dataclass
class FileUserSecretStore(UserSecretStore):
    file_store: FileStore
    path: str = 'secrets/{key}.json'
    jwt_secret: SecretStr

    async def save_secret(self, secret: UserSecret):
        json_str = secret.model_dump_json(context={'expose_secrets': True})
        await call_sync_from_async(self.file_store.write, self.path, json_str)

    async def load_secret(self, id: str) -> UserSecret | None:
        

    async def delete_secret(self, id: str) -> bool:
        """delete secret"""

    async def search(
        self,
        page_id: str | None = None,
        limit: int = 20,
    ) -> UserSecretResultSet:
        """Search secrets"""

    @classmethod
    @abstractmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> UserSecretStore:
        return FileUserSecretStore(
            file_store=get_file_store(config.file_store, config.file_store_path),
            jwt_secret=config.jwt_secret,
        )

    def _decrypt_value(self, value: SecretStr | str) -> str:
        fernet = self._fernet()
        if isinstance(value, SecretStr):
            return fernet.decrypt(
                b64decode(value.get_secret_value().encode())
            ).decode()
        else:
            return fernet.decrypt(b64decode(value.encode())).decode()

    def _encrypt_value(self, value: SecretStr | str) -> str:
        fernet = self._fernet()
        if isinstance(value, SecretStr):
            return b64encode(
                fernet.encrypt(value.get_secret_value().encode())
            ).decode()
        else:
            return b64encode(fernet.encrypt(value.encode())).decode()

    def _fernet(self):
        jwt_secret = self.config.jwt_secret.get_secret_value()
        fernet_key = b64encode(hashlib.sha256(jwt_secret.encode()).digest())
        return Fernet(fernet_key)
