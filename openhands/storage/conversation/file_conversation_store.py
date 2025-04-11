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
    ) -> ConversationMetadataResultSet:
        conversations: list[ConversationMetadata] = []
        metadata_dir = self.get_conversation_metadata_dir()
        try:
            # Get paths relative to base_path (e.g., sessions/sid1, sessions/sid2)
            listed_paths = self.file_store.list(metadata_dir)
            # Extract the directory name (sid) as the conversation ID
            conversation_ids = [
                Path(path).name # Use Path().name to get the last component
                for path in listed_paths
                # Ensure it's likely a session directory (simple check)
                if '/' in path and not path.startswith(f'{metadata_dir}/.')
            ]
        except FileNotFoundError:
            return ConversationMetadataResultSet([])
        # Remove duplicates just in case list returns unexpected variations
        conversation_ids = sorted(list(set(conversation_ids)))
        num_conversations = len(conversation_ids)
        start = page_id_to_offset(page_id)
        end = min(limit + start, num_conversations)
        conversations = []
        # Iterate through the calculated slice of potential IDs
        for conversation_id in conversation_ids[start:end]:
            try:
                # Check if metadata file exists before trying to load
                if await self.exists(conversation_id):
                    # Only append if metadata exists and loads correctly
                    conversations.append(await self.get_metadata(conversation_id))
                else:
                    # Log if the directory was listed but metadata is missing
                    logger.warning(f'Metadata file missing for listed conversation ID: {conversation_id}')
            except Exception as e:
                logger.warning(
                    f'Could not load conversation metadata for ID: {conversation_id}, Error: {e}'
                )
        # Sort the successfully loaded conversations
        conversations.sort(key=_sort_key, reverse=True)
        next_page_id = offset_to_page_id(end, end < num_conversations)
        return ConversationMetadataResultSet(conversations, next_page_id)

    def get_conversation_metadata_dir(self) -> str:
        return CONVERSATION_BASE_DIR

    def get_conversation_metadata_filename(self, conversation_id: str) -> str:
        return get_conversation_metadata_filename(conversation_id)

    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None, github_user_id: str | None
    ) -> FileConversationStore:
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileConversationStore(file_store)


def _sort_key(metadata: ConversationMetadata) -> float:
    """Sort by last_updated_at timestamp, handling potential None values."""
    if metadata.last_updated_at:
        # Assuming last_updated_at is datetime object
        return metadata.last_updated_at.timestamp()
    elif metadata.created_at:
         # Fallback to created_at if last_updated_at is missing
         return metadata.created_at.timestamp()
    return 0 # Fallback if both are missing
