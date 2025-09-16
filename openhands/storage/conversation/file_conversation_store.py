from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
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
    get_conversation_events_dir,
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
        try:
            json_str = await call_sync_from_async(self.file_store.read, path)
        except FileNotFoundError:
            # Attempt file-store-only fallback using events to synthesize minimal metadata
            synthesized = self._synthesize_metadata_from_events(conversation_id)
            if synthesized is not None:
                logger.debug(
                    f'Synthesized metadata for conversation without metadata.json: {conversation_id}'
                )
                return synthesized
            raise

        # Validate the JSON
        json_obj = json.loads(json_str)
        if 'created_at' not in json_obj:
            # Treat as missing metadata and try fallback
            synthesized = self._synthesize_metadata_from_events(conversation_id)
            if synthesized is not None:
                logger.debug(
                    f'Synthesized metadata for conversation with invalid metadata.json: {conversation_id}'
                )
                return synthesized
            raise FileNotFoundError(path)

        # Remove github_user_id if it exists
        if 'github_user_id' in json_obj:
            json_obj.pop('github_user_id')

        result = conversation_metadata_type_adapter.validate_python(json_obj)
        return result

    def _synthesize_metadata_from_events(
        self, conversation_id: str
    ) -> ConversationMetadata | None:
        """File-store-only fallback to synthesize minimal metadata when metadata.json is missing.

        Attempts to infer created_at from the earliest event file timestamp; uses directory
        mtime as a fallback. Only used inside FileConversationStore; other stores are unaffected.
        """
        try:
            events_dir = get_conversation_events_dir(conversation_id)
            event_entries = self.file_store.list(events_dir)
        except FileNotFoundError:
            # No events directory; use conversation directory mtime if available
            try:
                Path(self.get_conversation_metadata_filename(conversation_id)).parent
                # We cannot stat via FileStore, so use absence of events as a signal to skip
                # Fallback to returning None if we cannot infer anything reliably
                return None
            except Exception:
                return None

        # Filter to files that look like event files (e.g., .../events/<id>.json)
        event_files = [p for p in event_entries if p.endswith('.json')]
        if not event_files:
            return None

        # Determine earliest event id by filename and synthesize a created_at
        def _id_from_event_path(p: str) -> int:
            try:
                return int(Path(p).name.split('.')[0])
            except Exception:
                return 1_000_000_000

        earliest_event = min(event_files, key=_id_from_event_path)
        # Prefer actual event timestamp if available; otherwise fallback to now
        try:
            # Read the earliest event JSON and parse its timestamp
            evt_content = self.file_store.read(earliest_event)
            evt_obj = json.loads(evt_content)
            ts_str = evt_obj.get('timestamp')
            if isinstance(ts_str, str):
                created_at = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            else:
                created_at = datetime.now(timezone.utc)
        except Exception:
            created_at = datetime.now(timezone.utc)

        # Compose minimal metadata
        metadata = ConversationMetadata(
            conversation_id=conversation_id,
            selected_repository=None,
            user_id=None,
            title=None,
            created_at=created_at,
        )
        return metadata

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
            conversation_ids = [
                Path(path).name
                for path in self.file_store.list(metadata_dir)
                if not Path(path).name.startswith('.')
            ]
        except FileNotFoundError:
            return ConversationMetadataResultSet([])
        # Load valid conversations, then paginate based on valid count
        for conversation_id in conversation_ids:
            try:
                conversations.append(await self.get_metadata(conversation_id))
            except FileNotFoundError:
                # Common for CLI-created sessions that don't have metadata.json
                logger.debug(
                    f'Skipping conversation without metadata: {conversation_id}'
                )
            except Exception as e:
                logger.warning(
                    f'Could not load conversation metadata: {conversation_id} ({e})'
                )

        conversations.sort(key=_sort_key, reverse=True)
        total_valid = len(conversations)
        start = page_id_to_offset(page_id)
        end = min(limit + start, total_valid)
        conversations = conversations[start:end]
        next_page_id = offset_to_page_id(end, end < total_valid)
        return ConversationMetadataResultSet(conversations, next_page_id)

    def get_conversation_metadata_dir(self) -> str:
        return CONVERSATION_BASE_DIR

    def get_conversation_metadata_filename(self, conversation_id: str) -> str:
        return get_conversation_metadata_filename(conversation_id)

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
