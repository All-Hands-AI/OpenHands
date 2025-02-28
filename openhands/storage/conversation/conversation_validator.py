import os

from openhands.core.logger import openhands_logger as logger
from openhands.utils.import_utils import get_impl


class ConversationValidator:
    """Storage for conversation metadata. May or may not support multiple users depending on the environment."""

    async def validate(self, conversation_id: str, cookies_str: str):
        return None


conversation_validator_cls = os.environ.get(
    'OPENHANDS_CONVERSATION_VALIDATOR_CLS',
    'openhands.storage.conversation.conversation_validator.ConversationValidator',
)
logger.info(f'validator class: {conversation_validator_cls}')
ConversationValidatorImpl = get_impl(ConversationValidator, conversation_validator_cls)
