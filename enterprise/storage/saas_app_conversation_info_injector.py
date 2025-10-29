"""Enterprise injector for SQLAppConversationInfoService with SAAS filtering."""

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy import select
from storage.stored_conversation_metadata import StoredConversationMetadata
from storage.stored_conversation_metadata_saas import StoredConversationMetadataSaas

from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
    AppConversationInfoServiceInjector,
)
from openhands.app_server.app_conversation.sql_app_conversation_info_service import (
    SQLAppConversationInfoService,
)
from openhands.app_server.services.injector import InjectorState


class SaasSQLAppConversationInfoService(SQLAppConversationInfoService):
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


class SaasAppConversationInfoServiceInjector(AppConversationInfoServiceInjector):
    """Enterprise injector for SQLAppConversationInfoService with SAAS filtering."""

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[AppConversationInfoService, None]:
        from openhands.app_server.config import (
            get_db_session,
            get_user_context,
        )

        async with (
            get_user_context(state, request) as user_context,
            get_db_session(state, request) as db_session,
        ):
            service = SaasSQLAppConversationInfoService(
                db_session=db_session, user_context=user_context
            )
            yield service
