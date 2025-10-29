from sqlalchemy import select
from storage.stored_conversation_metadata_saas import StoredConversationMetadataSaas

from openhands.app_server.app_conversation.sql_app_conversation_info_service import (
    SQLAppConversationInfoService as _SQLAppConversationInfoService,
)
from openhands.app_server.app_conversation.sql_app_conversation_info_service import (
    StoredConversationMetadata as _StoredConversationMetadata,
)

StoredConversationMetadata = _StoredConversationMetadata


class SQLAppConversationInfoServiceSaas(_SQLAppConversationInfoService):
    """Extended SQLAppConversationInfoService with user-based filtering."""

    async def _secure_select(self):
        query = (
            select(StoredConversationMetadata)
            .join(
                StoredConversationMetadataSaas,
                StoredConversationMetadata.conversation_id
                == StoredConversationMetadataSaas.conversation_id,
            )
            .where(StoredConversationMetadata.conversation_version == 'V1')
        )

        user_id = await self.user_context.get_user_id()
        if user_id:
            query = query.where(StoredConversationMetadataSaas.user_id == user_id)

        return query


# Re-export for backward compatibility
SQLAppConversationInfoService = SQLAppConversationInfoServiceSaas


__all__ = ['StoredConversationMetadata', 'SQLAppConversationInfoService']
