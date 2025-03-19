import os

import jwt
from socketio.exceptions import ConnectionRefusedError

from openhands.server.auth import verify_token
from openhands.server.shared import config
from openhands.utils.import_utils import get_impl


class ConversationValidator:
    """Storage for conversation metadata. May or may not support multiple users depending on the environment."""

    async def validate(self, conversation_id: str, auth_info_str: str):
        if config.jwt_secret_client_auth:
            try:
                return verify_token(auth_info_str)
            except (
                jwt.ExpiredSignatureError,
                jwt.MissingRequiredClaimError,
                jwt.InvalidTokenError,
            ):
                raise ConnectionRefusedError('Invalid authentication token')
        return None, None


conversation_validator_cls = os.environ.get(
    'OPENHANDS_CONVERSATION_VALIDATOR_CLS',
    'openhands.storage.conversation.conversation_validator.ConversationValidator',
)
ConversationValidatorImpl = get_impl(ConversationValidator, conversation_validator_cls)
