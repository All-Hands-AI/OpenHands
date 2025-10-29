"""Enterprise injector for SQLAppConversationInfoService with SAAS filtering."""

from typing import AsyncGenerator

from fastapi import Request

from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
    AppConversationInfoServiceInjector,
)
from openhands.app_server.services.injector import InjectorState


class SaasAppConversationInfoServiceInjector(AppConversationInfoServiceInjector):
    """Enterprise injector for SQLAppConversationInfoService with SAAS filtering."""

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[AppConversationInfoService, None]:
        # Define inline to prevent circular lookup
        from storage.stored_conversation_metadata import (
            SQLAppConversationInfoServiceSaas,
        )

        from openhands.app_server.config import (
            get_db_session,
            get_user_context,
        )

        async with (
            get_user_context(state, request) as user_context,
            get_db_session(state, request) as db_session,
        ):
            service = SQLAppConversationInfoServiceSaas(
                db_session=db_session, user_context=user_context
            )
            yield service
