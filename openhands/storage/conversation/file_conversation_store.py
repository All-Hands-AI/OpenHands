from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import TypeAdapter

from openhands.core.config.app_config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.storage import get_file_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_metadata_result_set import (
    ConversationMetadataResultSet,
)
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    CONVERSATION_BASE_DIR,
    get_conversation_metadata_filename,
)
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.search_utils import offset_to_page_id, page_id_to_offset

conversation_metadata_type_adapter = TypeAdapter(ConversationMetadata)


@dataclass
class FileConversationStore(ConversationStore):
    file_store: FileStore
    user_id: str | None = None
    github_user_id: str | None = None

    async def save_metadata(self, metadata: ConversationMetadata) -> None:
        json_str = conversation_metadata_type_adapter.dump_json(metadata)
        path = self.get_conversation_metadata_filename(metadata.conversation_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        path = self.get_conversation_metadata_filename(conversation_id)
        json_str = await call_sync_from_async(self.file_store.read, path)

        # Temp: force int to str to stop pydandic being, well... pedantic
        json_obj = json.loads(json_str)
        if 'created_at' not in json_obj:
            raise FileNotFoundError(path)
        if isinstance(json_obj.get('github_user_id'), int):
            json_obj['github_user_id'] = str(json_obj.get('github_user_id'))

        result = conversation_metadata_type_adapter.validate_python(json_obj)
        return result

    async def delete_metadata(self, conversation_id: str) -> None:
        path = str(
            Path(self.get_conversation_metadata_filename(conversation_id)).parent
        )
        await call_sync_from_async(self.file_store.delete, path)

    async def exists(self, conversation_id: str) -> bool:
        path = self.get_conversation_metadata_filename(conversation_id)
        try:
            await call_sync_from_async(self.file_store.read, path)
            return True
        except FileNotFoundError:
            return False

    async def search(
        self,
        page_id: str | None = None,
        limit: int = 20,
        filter_conversation_ids: list[str] | None = None,
    ) -> ConversationMetadataResultSet:
        conversations: list[ConversationMetadata] = []
        metadata_dir = self.get_conversation_metadata_dir()
        try:
            conversation_ids = [
                path.split('/')[-2]
                for path in self.file_store.list(metadata_dir)
                if not path.startswith(f'{metadata_dir}/.')
            ]
        except FileNotFoundError:
            return ConversationMetadataResultSet([])

        if filter_conversation_ids:
            conversation_ids = list(
                set(conversation_ids) & set(filter_conversation_ids)
            )

        num_conversations = len(conversation_ids)
        start = page_id_to_offset(page_id)
        end = min(limit + start, num_conversations)
        conversations = []
        for conversation_id in conversation_ids:
            try:
                metadata = await self.get_metadata(conversation_id)
                # Only include conversations that belong to this user
                if (self.user_id and metadata.user_id == self.user_id) or (
                    self.github_user_id
                    and metadata.github_user_id == self.github_user_id
                ):
                    conversations.append(metadata)
            except Exception:
                logger.warning(
                    f'Could not load conversation metadata: {conversation_id}'
                )
        conversations.sort(key=_sort_key, reverse=True)
        if filter_conversation_ids:
            return ConversationMetadataResultSet(conversations, None)
        conversations = conversations[start:end]
        next_page_id = offset_to_page_id(end, end < num_conversations)
        return ConversationMetadataResultSet(conversations, next_page_id)

    def get_conversation_metadata_dir(self) -> str:
        if self.user_id:
            return f'users/{self.user_id}/conversations'
        return CONVERSATION_BASE_DIR

    def get_conversation_metadata_filename(self, conversation_id: str) -> str:
        return get_conversation_metadata_filename(conversation_id, self.user_id)

    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None, github_user_id: str | None
    ) -> FileConversationStore:
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileConversationStore(file_store, user_id, github_user_id)


def _sort_key(conversation: ConversationMetadata) -> str:
    created_at = conversation.created_at
    if created_at:
        return created_at.isoformat()  # YYYY-MM-DDTHH:MM:SS for sorting
    return ''
