from __future__ import annotations

import hashlib
import json
from base64 import b64decode, b64encode
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from pydantic import SecretStr

from openhands.core.config.app_config import AppConfig
from openhands.storage import get_file_store
from openhands.storage.data_models.user_secret import UserSecret
from openhands.storage.data_models.user_secret_result_set import UserSecretResultSet
from openhands.storage.files import FileStore
from openhands.storage.user_secret.user_secret_store import UserSecretStore
from openhands.utils.async_utils import call_sync_from_async, wait_all
from openhands.utils.search_utils import offset_to_page_id, page_id_to_offset


@dataclass
class FileUserSecretStore(UserSecretStore):
    file_store: FileStore
    jwt_secret: SecretStr
    path: str = 'secrets/'

    async def save_secret(self, secret: UserSecret):
        data = secret.model_dump(context={'expose_secrets': True})
        data['token_factory'] = self._encrypt_value(data['token_factory'])
        secret.updated_at = datetime.now(timezone.utc)
        data['updated_at'] = data['updated_at'].isoformat()
        data['created_at'] = data['created_at'].isoformat()
        json_str = json.dumps(data)
        path = self._file_path(secret.id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def load_secret(self, id: str) -> UserSecret | None:
        try:
            path = self._file_path(id)
            kwargs = json.loads(self.file_store.read(path))
            kwargs['token_factory'] = self._decrypt_value(kwargs['token_factory'])
            kwargs['updated_at'] = datetime.fromisoformat(kwargs['updated_at'])
            kwargs['created_at'] = datetime.fromisoformat(kwargs['created_at'])
            result = UserSecret(**kwargs)
            return result
        except FileNotFoundError:
            return None

    async def delete_secret(self, id: str) -> bool:
        path = self._file_path(id)
        try:
            self.file_store.delete(path)
            return True
        except FileNotFoundError:
            return False

    async def search(
        self,
        page_id: str | None = None,
        limit: int = 20,
    ) -> UserSecretResultSet:
        try:
            secret_ids = [
                path.split('/')[-1].split('.')[0]
                for path in self.file_store.list(self.path)
            ]
        except FileNotFoundError:
            return UserSecretResultSet([])
        num_secrets = len(secret_ids)
        start = page_id_to_offset(page_id)
        end = min(limit + start, num_secrets)
        result_set = UserSecretResultSet(
            results=await wait_all(
                [self.load_secret(secret_id) for secret_id in secret_ids[start:end]]
            ),
            next_page_id=offset_to_page_id(end, end < num_secrets),
        )
        return result_set

    def _file_path(self, id: str) -> str:
        return f'{self.path}{id}.json'

    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> UserSecretStore:
        return FileUserSecretStore(
            file_store=get_file_store(config.file_store, config.file_store_path),
            jwt_secret=config.jwt_secret,
        )

    def _decrypt_value(self, value: str) -> dict:
        fernet = self._fernet()
        value_json = fernet.decrypt(b64decode(value.encode())).decode()
        result = json.loads(value_json)
        return result

    def _encrypt_value(self, value: dict) -> str:
        value_json = json.dumps(value)
        fernet = self._fernet()
        return b64encode(fernet.encrypt(value_json.encode())).decode()

    def _fernet(self):
        jwt_secret = self.jwt_secret.get_secret_value()
        fernet_key = b64encode(hashlib.sha256(jwt_secret.encode()).digest())
        return Fernet(fernet_key)
