import json
from dataclasses import dataclass

from openhands.core.config.app_config import AppConfig
from openhands.storage import get_file_store
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_metadata_filename
from openhands.utils.async_utils import call_sync_from_async


@dataclass
class ConversationMetadata:
    conversation_id: str
    github_user_id: str
    selected_repository: str | None


@dataclass
class ConversationStore:
    file_store: FileStore

    async def save_metadata(self, metadata: ConversationMetadata):
        json_str = json.dumps(metadata.__dict__)
        path = get_conversation_metadata_filename(metadata.conversation_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        path = get_conversation_metadata_filename(conversation_id)
        json_str = await call_sync_from_async(self.file_store.read, path)
        return ConversationMetadata(**json.loads(json_str))

    async def exists(self, conversation_id: str) -> bool:
        path = get_conversation_metadata_filename(conversation_id)
        try:
            await call_sync_from_async(self.file_store.read, path)
            return True
        except FileNotFoundError:
            return False

    @classmethod
    async def get_instance(cls, config: AppConfig):
        file_store = get_file_store(config.file_store, config.file_store_path)
        return ConversationStore(file_store)
