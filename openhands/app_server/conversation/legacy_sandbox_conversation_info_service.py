import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import UUID

from fastapi import Depends

from openhands.app_server.conversation.conversation_models import (
    SandboxedConversationInfo,
    SandboxedConversationInfoPage,
)
from openhands.app_server.conversation.sandboxed_conversation_info_service import (
    SandboxedConversationInfoService,
    SandboxedConversationInfoServiceResolver,
)
from openhands.llm.metrics import TokenUsage
from openhands.sdk.llm import MetricsSnapshot
from openhands.server.utils import get_conversation_store
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.data_models.conversation_metadata import ConversationMetadata

CONVERSATION_VERSION = 'V1'


@dataclass
class LegacySandboxedConversationInfoService(SandboxedConversationInfoService):
    """Adapter for conversations within the legacy API which do not contain status info.
    We should replace this with direct SQL access as soon as both the OSS and SAAS
    use SQL. As it is, what we have is not really async (As the db connection
    in ConversationStore is not async), but I doubt it will cause issues.
    """

    conversation_store: ConversationStore

    async def search_sandboxed_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        page_id: str | None = None,
        limit: int = 20,
    ) -> SandboxedConversationInfoPage:
        """Search for sandboxed conversations."""
        result_set = await self.conversation_store.search(page_id=page_id, limit=limit)
        results = result_set.results

        # Apply Filters... (This will be pure sql when we stop using legacy...)
        items = []
        for meta in results:
            if title__contains and title__contains not in (meta.title or ''):
                continue
            if (
                created_at__gte
                and meta.created_at
                and created_at__gte > meta.created_at
            ):
                continue
            if created_at__lt and meta.created_at and created_at__lt <= meta.created_at:
                continue
            if (
                updated_at__gte
                and meta.last_updated_at
                and updated_at__gte > meta.last_updated_at
            ):
                continue
            if (
                updated_at__lt
                and meta.last_updated_at
                and updated_at__lt <= meta.last_updated_at
            ):
                continue
            if meta.conversation_version != CONVERSATION_VERSION:
                continue
            items.append(self._to_conversation_info(meta))

        return SandboxedConversationInfoPage(
            items=items, next_page_id=result_set.next_page_id
        )

    async def count_sandboxed_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        count = 0
        page_id = None
        while True:
            result_set = await self.search_sandboxed_conversation_info(
                title__contains=title__contains,
                created_at__gte=created_at__gte,
                created_at__lt=created_at__lt,
                updated_at__gte=updated_at__gte,
                updated_at__lt=updated_at__lt,
                page_id=page_id,
            )
            count += len(result_set.items)
            page_id = result_set.next_page_id
            if not page_id:
                return count

    async def get_sandboxed_conversation_info(
        self, conversation_id: UUID
    ) -> SandboxedConversationInfo | None:
        try:
            metadata = await self.conversation_store.get_metadata(conversation_id.hex)
            if metadata.conversation_version != CONVERSATION_VERSION:
                return None
            info = self._to_conversation_info(metadata)
            return info
        except Exception:
            return None

    async def batch_get_sandboxed_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[SandboxedConversationInfo | None]:
        """Get a batch of sandboxed conversations. Return None for any conversation
        which was not found.
        """
        return await asyncio.gather(
            *[
                self.get_sandboxed_conversation_info(conversation_id)
                for conversation_id in conversation_ids
            ]
        )

    async def save_sandboxed_conversation_info(self, info: SandboxedConversationInfo):
        metrics = info.metrics or MetricsSnapshot()
        token_usage = metrics.accumulated_token_usage or TokenUsage()

        metadata = ConversationMetadata(
            conversation_id=info.id.hex,
            title=info.title,
            selected_repository=info.selected_repository,
            user_id=info.user_id,
            selected_branch=info.selected_branch,
            git_provider=info.git_provider,
            trigger=info.trigger,
            pr_number=info.pr_number,
            llm_model=info.llm_model,
            accumulated_cost=metrics.accumulated_cost,
            prompt_tokens=token_usage.prompt_tokens,
            completion_tokens=token_usage.completion_tokens,
            total_tokens=(
                token_usage.prompt_tokens
                + token_usage.completion_tokens
                + token_usage.cache_read_tokens
                + token_usage.cache_write_tokens
            ),
            sandbox_id=info.sandbox_id,
            created_at=info.created_at,
            last_updated_at=info.updated_at,
        )
        await self.conversation_store.save_metadata(metadata)

    def _to_conversation_info(self, meta: ConversationMetadata):
        return SandboxedConversationInfo(
            id=meta.conversation_id,
            title=meta.title,
            selected_repository=meta.selected_repository,
            user_id=meta.user_id,
            selected_branch=meta.selected_branch,
            git_provider=meta.git_provider,
            trigger=meta.trigger,
            pr_number=meta.pr_number,
            llm_model=meta.llm_model,
            metrics=MetricsSnapshot(
                model_name=meta.llm_model,
                accumulated_cost=meta.accumulated_cost,
                accumulated_token_usage=TokenUsage(
                    model=meta.llm_model or '',
                    prompt_tokens=meta.prompt_tokens,
                    completion_tokens=meta.completion_tokens,
                    # TODO: This is incomplete because we calculate tokens differently in agent sdk
                ),
            ),
            sandbox_id=meta.sandbox_id,
            created_at=meta.created_at,
            updated_at=meta.last_updated_at,
        )

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Stop using this sandboxed conversation info service"""
        pass


class LegacySandboxedConversationInfoServiceResolver(
    SandboxedConversationInfoServiceResolver
):
    def get_resolver_for_user(self) -> Callable:
        return self._resolve_for_user

    def _resolve_for_user(
        self,
        conversation_store: ConversationStore = Depends(get_conversation_store),
    ) -> SandboxedConversationInfoService:
        return LegacySandboxedConversationInfoService(conversation_store)
