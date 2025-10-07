"""SQL implementation of AppConversationService.

This implementation provides CRUD operations for sandboxed conversations focused purely
on SQL operations:
- Direct database access without permission checks
- Batch operations for efficient data retrieval
- Integration with SandboxService for sandbox information
- HTTP client integration for agent status retrieval
- Full async/await support using SQL async sessions

Security and permission checks are handled by wrapper services.

Key components:
- SQLAppConversationService: Main service class implementing all operations
- SQLAppConversationInfoServiceInjector: Dependency injection resolver for FastAPI
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Column, DateTime, Float, Integer, Select, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.agent_server.utils import utc_now
from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
    AppConversationInfoServiceInjector,
)
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
    AppConversationInfoPage,
    AppConversationSortOrder,
)
from openhands.app_server.user.user_context import UserContext
from openhands.app_server.utils.sql_utils import (
    Base,
    create_json_type_decorator,
)
from openhands.integrations.provider import ProviderType
from openhands.sdk.llm import MetricsSnapshot
from openhands.sdk.llm.utils.metrics import TokenUsage
from openhands.storage.data_models.conversation_metadata import ConversationTrigger

logger = logging.getLogger(__name__)


class StoredConversationMetadata(Base):  # type: ignore
    __tablename__ = 'conversation_metadata'
    conversation_id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    github_user_id = Column(String, nullable=True)  # The GitHub user ID
    user_id = Column(String, nullable=False)  # The Keycloak User ID
    selected_repository = Column(String, nullable=True)
    selected_branch = Column(String, nullable=True)
    git_provider = Column(
        String, nullable=True
    )  # The git provider (GitHub, GitLab, etc.)
    title = Column(String, nullable=True)
    last_updated_at = Column(DateTime(timezone=True), default=utc_now)  # type: ignore[attr-defined]
    created_at = Column(DateTime(timezone=True), default=utc_now)  # type: ignore[attr-defined]

    trigger = Column(String, nullable=True)
    pr_number = Column(create_json_type_decorator(list[int]))

    # Cost and token metrics
    accumulated_cost = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    max_budget_per_task = Column(Float, nullable=True)
    cache_read_tokens = Column(Integer, default=0)
    cache_write_tokens = Column(Integer, default=0)
    reasoning_tokens = Column(Integer, default=0)
    context_window = Column(Integer, default=0)
    per_turn_token = Column(Integer, default=0)

    # LLM model used for the conversation
    llm_model = Column(String, nullable=True)

    conversation_version = Column(String, nullable=False, default='V0', index=True)
    sandbox_id = Column(String, nullable=True, index=True)


@dataclass
class SQLAppConversationInfoService(AppConversationInfoService):
    """SQL implementation of AppConversationInfoService focused on db operations.

    This allows storing a record of a conversation even after its sandbox ceases to exist
    """

    session: AsyncSession
    user_id: str | None = None

    async def search_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        sort_order: AppConversationSortOrder = AppConversationSortOrder.CREATED_AT_DESC,
        page_id: str | None = None,
        limit: int = 100,
    ) -> AppConversationInfoPage:
        """Search for sandboxed conversations without permission checks."""
        query = self._secure_select()

        query = self._apply_filters(
            query=query,
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
        )

        # Add sort order
        if sort_order == AppConversationSortOrder.CREATED_AT:
            query = query.order_by(StoredConversationMetadata.created_at)
        elif sort_order == AppConversationSortOrder.CREATED_AT_DESC:
            query = query.order_by(StoredConversationMetadata.created_at.desc())
        elif sort_order == AppConversationSortOrder.UPDATED_AT:
            query = query.order_by(StoredConversationMetadata.updated_at)
        elif sort_order == AppConversationSortOrder.UPDATED_AT_DESC:
            query = query.order_by(StoredConversationMetadata.updated_at.desc())
        elif sort_order == AppConversationSortOrder.TITLE:
            query = query.order_by(StoredConversationMetadata.title)
        elif sort_order == AppConversationSortOrder.TITLE_DESC:
            query = query.order_by(StoredConversationMetadata.title.desc())

        # Apply pagination
        if page_id is not None:
            try:
                offset = int(page_id)
                query = query.offset(offset)
            except ValueError:
                # If page_id is not a valid integer, start from beginning
                offset = 0
        else:
            offset = 0

        # Apply limit and get one extra to check if there are more results
        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        rows = result.scalars().all()

        # Check if there are more results
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [self._to_info(row) for row in rows]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        return AppConversationInfoPage(items=items, next_page_id=next_page_id)

    async def count_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        """Count sandboxed conversations matching the given filters."""
        query = select(func.count(StoredConversationMetadata.conversation_id))
        if self.user_id:
            query = query.where(
                StoredConversationMetadata.created_by_user_id == self.user_id
            )

        query = self._apply_filters(
            query=query,
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
        )

        result = await self.session.execute(query)
        count = result.scalar()
        return count or 0

    def _apply_filters(
        self,
        query: Select,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> Select:
        # Apply the same filters as search_app_conversations
        conditions = []
        if title__contains is not None:
            conditions.append(
                StoredConversationMetadata.title.like(f'%{title__contains}%')
            )

        if created_at__gte is not None:
            conditions.append(StoredConversationMetadata.created_at >= created_at__gte)

        if created_at__lt is not None:
            conditions.append(StoredConversationMetadata.created_at < created_at__lt)

        if updated_at__gte is not None:
            conditions.append(
                StoredConversationMetadata.last_updated_at >= updated_at__gte
            )

        if updated_at__lt is not None:
            conditions.append(
                StoredConversationMetadata.last_updated_at < updated_at__lt
            )

        if conditions:
            query = query.where(*conditions)
        return query

    async def get_app_conversation_info(
        self, conversation_id: UUID
    ) -> AppConversationInfo | None:
        query = self._secure_select().where(
            StoredConversationMetadata.conversation_id == str(conversation_id)
        )
        result_set = await self.session.execute(query)
        result = result_set.scalar_one_or_none()
        if result:
            return self._to_info(result)
        return None

    async def batch_get_app_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversationInfo | None]:
        conversation_id_strs = [
            str(conversation_id) for conversation_id in conversation_ids
        ]
        query = self._secure_select().where(
            StoredConversationMetadata.conversation_id.in_(conversation_id_strs)
        )
        result = await self.session.execute(query)
        rows = result.scalars().all()
        info_by_id = {info.conversation_id: info for info in rows if info}
        results: list[AppConversationInfo | None] = []
        for conversation_id in conversation_id_strs:
            info = info_by_id.get(conversation_id)
            if info:
                results.append(self._to_info(info))
            else:
                results.append(None)

        return results

    async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        if self.user_id:
            query = select(StoredConversationMetadata).where(
                StoredConversationMetadata.conversation_id == info.id
            )
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            assert existing is None or existing.created_by_user_id == self.user_id

        metrics = info.metrics or MetricsSnapshot()
        usage = metrics.accumulated_token_usage or TokenUsage()

        stored = StoredConversationMetadata(
            conversation_id=str(info.id),
            github_user_id=None,  # TODO: Should we add this to the conversation info?
            user_id=info.created_by_user_id,
            selected_repository=info.selected_repository,
            selected_branch=info.selected_branch,
            git_provider=info.git_provider.value if info.git_provider else None,
            title=info.title,
            last_updated_at=info.updated_at,
            created_at=info.created_at,
            trigger=info.trigger.value if info.trigger else None,
            pr_number=info.pr_number,
            # Cost and token metrics
            accumulated_cost=metrics.accumulated_cost,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=0,
            max_budget_per_task=metrics.max_budget_per_task,
            cache_read_tokens=usage.cache_read_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            context_window=usage.context_window,
            per_turn_token=usage.per_turn_token,
            llm_model=info.llm_model,
            conversation_version='V1',
            sandbox_id=info.sandbox_id,
        )

        await self.session.merge(stored)
        await self.session.commit()
        return info

    def _secure_select(self):
        query = select(StoredConversationMetadata).where(
            StoredConversationMetadata.conversation_version == 'V1'
        )
        if self.user_id:
            query = query.where(
                StoredConversationMetadata.user_id == self.user_id,
            )
        return query

    def _to_info(self, stored: StoredConversationMetadata) -> AppConversationInfo:
        # V1 conversations should always have a sandbox_id
        sandbox_id = stored.sandbox_id
        assert sandbox_id is not None

        # Rebuild token usage
        token_usage = TokenUsage(
            prompt_tokens=stored.prompt_tokens,
            completion_tokens=stored.completion_tokens,
            cache_read_tokens=stored.cache_read_tokens,
            cache_write_tokens=stored.cache_write_tokens,
            context_window=stored.context_window,
            per_turn_token=stored.per_turn_token,
        )

        # Rebuild metrics object
        metrics = MetricsSnapshot(
            accumulated_cost=stored.accumulated_cost,
            max_budget_per_task=stored.max_budget_per_task,
            accumulated_token_usage=token_usage,
        )

        return AppConversationInfo(
            id=UUID(stored.conversation_id),
            created_by_user_id=stored.user_id,
            sandbox_id=stored.sandbox_id,
            selected_repository=stored.selected_repository,
            selected_branch=stored.selected_branch,
            git_provider=ProviderType(stored.git_provider)
            if stored.git_provider
            else None,
            title=stored.title,
            trigger=ConversationTrigger(stored.trigger) if stored.trigger else None,
            pr_number=stored.pr_number,
            llm_model=stored.llm_model,
            metrics=metrics,
            created_at=stored.created_at,
            updated_at=stored.last_updated_at,
        )


class SQLAppConversationInfoServiceInjector(AppConversationInfoServiceInjector):
    def get_injector(self) -> Callable[..., Awaitable[AppConversationInfoService]]:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import db_service, user_injector

        # Create dependencies at module level to avoid B008
        user_dependency = Depends(user_injector())
        _db_dependency = Depends(db_service().managed_session_dependency)

        async def resolve_app_conversation_service(
            user_context: UserContext = user_dependency,
            session: AsyncSession = _db_dependency,
        ) -> AppConversationInfoService:
            user_id = await user_context.get_user_id()
            service = SQLAppConversationInfoService(session=session, user_id=user_id)
            return service

        return resolve_app_conversation_service
