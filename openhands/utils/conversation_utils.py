from datetime import datetime
from typing import Callable

from openhands.core.logger import openhands_logger as logger
from openhands.server.routes.settings import ConversationStoreImpl
from openhands.server.shared import config
from openhands.storage.data_models.conversation_info import ConversationInfo
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_status import ConversationStatus
from openhands.utils.async_utils import GENERAL_TIMEOUT, call_async_from_sync


async def get_conversation_info(
    conversation: ConversationMetadata,
    is_running: bool,
) -> ConversationInfo | None:
    try:
        title = conversation.title
        if not title:
            title = f'Conversation {conversation.conversation_id}'
        return ConversationInfo(
            id=conversation.conversation_id,
            title=title,
            last_updated_at=conversation.last_updated_at,
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


def create_conversation_update_callback(
    github_token: str, conversation_id: str
) -> Callable:
    def callback(*args, **kwargs):
        call_async_from_sync(
            update_timestamp_for_conversation,
            GENERAL_TIMEOUT,
            github_token,
            conversation_id,
        )

    return callback


async def update_timestamp_for_conversation(github_token: str, conversation_id: str):
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    conversation = await conversation_store.get_metadata(conversation_id)
    conversation.last_updated_at = datetime.now()
    await conversation_store.save_metadata(conversation)
