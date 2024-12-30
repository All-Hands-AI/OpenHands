from __future__ import annotations

import json
from dataclasses import dataclass

from openhands.core.config.app_config import AppConfig
from openhands.storage import get_file_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.server.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_metadata_filename
from openhands.utils.async_utils import call_sync_from_async


@dataclass
class FileConversationStore(ConversationStore):
    file_store: FileStore

    async def save_metadata(self, metadata: ConversationMetadata):
        json_str = json.dumps(metadata.__dict__)
        path = self.get_conversation_metadata_filename(metadata.conversation_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        path = self.get_conversation_metadata_filename(conversation_id)
        json_str = await call_sync_from_async(self.file_store.read, path)
        return ConversationMetadata(**json.loads(json_str))

    async def exists(self, conversation_id: str) -> bool:
        path = self.get_conversation_metadata_filename(conversation_id)
        try:
            await call_sync_from_async(self.file_store.read, path)
            return True
        except FileNotFoundError:
            return False

    def get_conversation_metadata_filename(self, conversation_id: str) -> str:
        return get_conversation_metadata_filename(conversation_id)

    @classmethod
    async def get_instance(cls, config: AppConfig, token: str | None):
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileConversationStore(file_store)
