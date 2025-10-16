from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import TypeAdapter

from openhands.core.config.openhands_config import OpenHandsConfig
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
    _deleting_conversations: set[str] = field(default_factory=set)
    _deletion_lock: threading.Lock = field(default_factory=threading.Lock)

    async def save_metadata(self, metadata: ConversationMetadata) -> None:
        json_str = conversation_metadata_type_adapter.dump_json(metadata)
        path = self.get_conversation_metadata_filename(metadata.conversation_id)
        await call_sync_from_async(self.file_store.write, path, json_str)

    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        path = self.get_conversation_metadata_filename(conversation_id)
        json_str = await call_sync_from_async(self.file_store.read, path)

        # Validate the JSON
        json_obj = json.loads(json_str)
        if 'created_at' not in json_obj:
            raise FileNotFoundError(path)

        # Remove github_user_id if it exists
        if 'github_user_id' in json_obj:
            json_obj.pop('github_user_id')

        result = conversation_metadata_type_adapter.validate_python(json_obj)
        return result

    async def delete_metadata(self, conversation_id: str) -> None:
        # Mark conversation as being deleted to prevent race conditions
        with self._deletion_lock:
            self._deleting_conversations.add(conversation_id)

        try:
            path = str(
                Path(self.get_conversation_metadata_filename(conversation_id)).parent
            )
            await call_sync_from_async(self.file_store.delete, path)
        finally:
            # Remove from deleting set after deletion is complete
            with self._deletion_lock:
                self._deleting_conversations.discard(conversation_id)

    async def exists(self, conversation_id: str) -> bool:
        # Don't check deletion status for exists() - this is used during conversation creation
        # and we don't want to block new conversations if there's a stale deletion entry
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
            conversation_ids = [
                Path(path).name
                for path in self.file_store.list(metadata_dir)
                if not Path(path).name.startswith('.')
            ]
        except FileNotFoundError:
            return ConversationMetadataResultSet([])
        num_conversations = len(conversation_ids)
        start = page_id_to_offset(page_id)
        end = min(limit + start, num_conversations)
        conversations = []
        orphaned_dirs = []  # Track directories that should be cleaned up

        for conversation_id in conversation_ids:
            try:
                conversations.append(await self.get_metadata(conversation_id))
            except FileNotFoundError:
                # This is likely a race condition where the directory exists but metadata.json is missing
                # This happens when delete_conversation removes the directory but other operations
                # recreate it without the metadata.json file
                logger.debug(
                    f'Skipping conversation with missing metadata.json (race condition): {conversation_id}'
                )
                orphaned_dirs.append(conversation_id)
            except json.JSONDecodeError as e:
                logger.warning(
                    f'Invalid JSON in conversation metadata for {conversation_id}: {e}'
                )
            except Exception as e:
                logger.warning(
                    f'Could not load conversation metadata for {conversation_id}: {e}'
                )

        # Clean up orphaned directories in the background
        if orphaned_dirs:
            logger.info(
                f'Found {len(orphaned_dirs)} orphaned conversation directories, scheduling cleanup'
            )
            # Schedule cleanup in background to avoid blocking the search operation
            import asyncio

            asyncio.create_task(self._cleanup_orphaned_directories(orphaned_dirs))

        # Clean up stale deletion entries to prevent blocking new conversations
        self._cleanup_stale_deletion_entries()

        conversations.sort(key=_sort_key, reverse=True)
        conversations = conversations[start:end]
        next_page_id = offset_to_page_id(end, end < num_conversations)
        return ConversationMetadataResultSet(conversations, next_page_id)

    def get_conversation_metadata_dir(self) -> str:
        return CONVERSATION_BASE_DIR

    def get_conversation_metadata_filename(self, conversation_id: str) -> str:
        return get_conversation_metadata_filename(conversation_id)

    def _is_conversation_being_deleted(self, conversation_id: str) -> bool:
        """Check if a conversation is currently being deleted.

        This helps prevent race conditions where other operations try to write
        to a conversation directory while it's being deleted.
        """
        with self._deletion_lock:
            return conversation_id in self._deleting_conversations

    def _cleanup_stale_deletion_entries(self) -> None:
        """Clean up stale deletion entries that might be blocking new conversations.

        This is a safety mechanism to prevent deletion tracking from getting stuck.
        """
        with self._deletion_lock:
            # Remove any conversation IDs that are no longer being actively deleted
            # This is a simple cleanup - in a production system you might want more sophisticated tracking
            if (
                len(self._deleting_conversations) > 100
            ):  # Arbitrary limit to prevent memory issues
                logger.warning(
                    f'Clearing {len(self._deleting_conversations)} stale deletion entries'
                )
                self._deleting_conversations.clear()

    async def _cleanup_orphaned_directories(self, conversation_ids: list[str]) -> None:
        """Clean up orphaned conversation directories that have no metadata.json file.

        This handles the race condition where delete_conversation removes a directory
        but other operations recreate it without the metadata.json file.
        """
        for conversation_id in conversation_ids:
            try:
                # Skip if conversation is currently being deleted
                if self._is_conversation_being_deleted(conversation_id):
                    logger.debug(
                        f'Conversation {conversation_id} is being deleted, skipping cleanup'
                    )
                    continue

                # Double-check that the directory is truly orphaned
                if await self._is_directory_orphaned(conversation_id):
                    logger.info(
                        f'Cleaning up orphaned conversation directory: {conversation_id}'
                    )
                    await self.delete_metadata(conversation_id)
                else:
                    logger.debug(
                        f'Directory {conversation_id} is not orphaned, skipping cleanup'
                    )
            except Exception as e:
                logger.warning(
                    f'Error cleaning up orphaned directory {conversation_id}: {e}'
                )

    async def _is_directory_orphaned(self, conversation_id: str) -> bool:
        """Check if a conversation directory is orphaned (has no metadata.json file).

        Returns True if the directory exists but has no metadata.json file.
        """
        try:
            # Check if metadata.json exists
            await self.get_metadata(conversation_id)
            return False  # Metadata exists, not orphaned
        except FileNotFoundError:
            # Check if the directory exists at all
            try:
                conversation_dir = str(
                    Path(
                        self.get_conversation_metadata_filename(conversation_id)
                    ).parent
                )
                await call_sync_from_async(self.file_store.list, conversation_dir)
                return True  # Directory exists but no metadata.json
            except FileNotFoundError:
                return False  # Directory doesn't exist at all
        except Exception:
            return False  # Other errors, assume not orphaned

    @classmethod
    async def get_instance(
        cls, config: OpenHandsConfig, user_id: str | None
    ) -> FileConversationStore:
        file_store = get_file_store(
            file_store_type=config.file_store,
            file_store_path=config.file_store_path,
            file_store_web_hook_url=config.file_store_web_hook_url,
            file_store_web_hook_headers=config.file_store_web_hook_headers,
            file_store_web_hook_batch=config.file_store_web_hook_batch,
        )
        return FileConversationStore(file_store)


def _sort_key(conversation: ConversationMetadata) -> str:
    created_at = conversation.created_at
    if created_at:
        return created_at.isoformat()  # YYYY-MM-DDTHH:MM:SS for sorting
    return ''
