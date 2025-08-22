import os
from datetime import datetime, timezone

from openhands.core.config.utils import load_openhands_config
from openhands.core.logger import openhands_logger as logger
from openhands.server.config.server_config import ServerConfig
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.utils.conversation_summary import get_default_conversation_title
from openhands.utils.import_utils import get_impl


class ConversationValidator:
    """Abstract base class for validating conversation access.

    This is an extension point in OpenHands that allows applications to customize how
    conversation access is validated. Applications can substitute their own implementation by:
    1. Creating a class that inherits from ConversationValidator
    2. Implementing the validate method
    3. Setting OPENHANDS_CONVERSATION_VALIDATOR_CLS environment variable to the fully qualified name of the class

    The class is instantiated via get_impl() in create_conversation_validator().

    The default implementation performs no validation and returns None, None.
    """

    async def validate(
        self,
        conversation_id: str,
        cookies_str: str,
        authorization_header: str | None = None,
    ) -> str | None:
        user_id = None
        metadata = await self._ensure_metadata_exists(conversation_id, user_id)
        return metadata.user_id

    async def _ensure_metadata_exists(
        self,
        conversation_id: str,
        user_id: str | None,
    ) -> ConversationMetadata:
        config = load_openhands_config()
        server_config = ServerConfig()

        conversation_store_class: type[ConversationStore] = get_impl(
            ConversationStore,
            server_config.conversation_store_class,
        )
        conversation_store = await conversation_store_class.get_instance(
            config, user_id
        )

        try:
            metadata = await conversation_store.get_metadata(conversation_id)
        except FileNotFoundError:
            logger.info(
                f'Creating new conversation metadata for {conversation_id}',
                extra={'session_id': conversation_id},
            )
            await conversation_store.save_metadata(
                ConversationMetadata(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title=get_default_conversation_title(conversation_id),
                    last_updated_at=datetime.now(timezone.utc),
                    selected_repository=None,
                )
            )
            metadata = await conversation_store.get_metadata(conversation_id)
        return metadata


def create_conversation_validator() -> ConversationValidator:
    conversation_validator_cls = os.environ.get(
        'OPENHANDS_CONVERSATION_VALIDATOR_CLS',
        'openhands.storage.conversation.conversation_validator.ConversationValidator',
    )
    ConversationValidatorImpl = get_impl(
        ConversationValidator, conversation_validator_cls
    )
    return ConversationValidatorImpl()
