import json
from datetime import datetime

from openhands.core.logger import openhands_logger as logger
from openhands.server.shared import session_manager
from openhands.storage.data_models.conversation_info import ConversationInfo
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.storage.locations import get_conversation_events_dir


async def get_conversation_info(
    conversation: ConversationMetadata,
    is_running: bool,
) -> ConversationInfo | None:
    try:
        file_store = session_manager.file_store
        events_dir = get_conversation_events_dir(conversation.conversation_id)
        events = file_store.list(events_dir)
        events = sorted(events)
        event_path = events[-1]
        event = json.loads(file_store.read(event_path))
        title = conversation.title
        if not title:
            title = f'Conversation {conversation.conversation_id}'
        return ConversationInfo(
            id=conversation.conversation_id,
            title=title,
            last_updated_at=datetime.fromisoformat(event.get('timestamp')),
            selected_repository=conversation.selected_repository,
            status=ConversationStatus.RUNNING
            if is_running
            else ConversationStatus.STOPPED,
        )
    except Exception:  # type: ignore
        logger.warning(
            f'Error loading conversation: {conversation.conversation_id}',
            exc_info=True,
            stack_info=True,
        )
        return None
