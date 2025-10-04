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
- SQLAppConversationServiceManager: Dependency injection resolver for FastAPI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Column, Select, String, func, select, UUID as SQLUUID
from sqlalchemy.ext.asyncio import AsyncSession
from openhands.sdk.llm import MetricsSnapshot

from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
    AppConversationInfoServiceManager,
)
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
    AppConversationInfoPage,
    AppConversationSortOrder,
)
from openhands.app_server.user.user_service import UserService
from openhands.app_server.utils.sql_utils import Base, UtcDateTime, create_enum_type_decorator, create_json_type_decorator, row2dict
from openhands.integrations.service_types import ProviderType
from openhands.storage.data_models.conversation_metadata import ConversationTrigger

logger = logging.getLogger(__name__)



class StoredAppConversationInfo(Base):  # type: ignore
    __tablename__ = "v1_app_conversation_info"
    id = Column(SQLUUID, primary_key=True)
    created_by_user_id = Column(String, index=True)
    selected_repository = Column(String, nullable=True)
    selected_branch = Column(String, nullable=True)
    git_provider = Column(create_enum_type_decorator(ProviderType), nullable=True)
    title = Column(String, nullable=True)
    trigger = Column(create_enum_type_decorator(ConversationTrigger), nullable=True)
    pr_number = Column(create_json_type_decorator(list[int]))
    llm_model = Column(String, nullable=True)
    metrics = Column(create_json_type_decorator(MetricsSnapshot))
    sandbox_id = Column(String, index=True)
    created_at = Column(UtcDateTime, server_default=func.now(), index=True)
    updated_at = Column(UtcDateTime, onupdate=func.now(), index=True)


@dataclass
class SQLAppConversationInfoService(AppConversationInfoService):
    """SQL implementation of AppConversationInfoService focused on db operations.

    This allows storing a record of a conversation even after its sandbox ceases to exist"""

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
            query = query.order_by(StoredAppConversationInfo.created_at)
        elif sort_order == AppConversationSortOrder.CREATED_AT_DESC:
            query = query.order_by(StoredAppConversationInfo.created_at.desc())
        elif sort_order == AppConversationSortOrder.UPDATED_AT:
            query = query.order_by(StoredAppConversationInfo.updated_at)
        elif sort_order == AppConversationSortOrder.UPDATED_AT_DESC:
            query = query.order_by(StoredAppConversationInfo.updated_at.desc())
        elif sort_order == AppConversationSortOrder.TITLE:
            query = query.order_by(StoredAppConversationInfo.title)
        elif sort_order == AppConversationSortOrder.TITLE_DESC:
            query = query.order_by(StoredAppConversationInfo.title.desc())

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
        rows = list(result)

        # Check if there are more results
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [
            AppConversationInfo(**row2dict(row)) for row in rows
        ]

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
        query = self._secure_select()

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
                StoredAppConversationInfo.title.like(f'%{title__contains}%')
            )

        if created_at__gte is not None:
            conditions.append(StoredAppConversationInfo.created_at >= created_at__gte)

        if created_at__lt is not None:
            conditions.append(StoredAppConversationInfo.created_at < created_at__lt)

        if updated_at__gte is not None:
            conditions.append(StoredAppConversationInfo.updated_at >= updated_at__gte)

        if updated_at__lt is not None:
            conditions.append(StoredAppConversationInfo.updated_at < updated_at__lt)

        if conditions:
            query = query.where(*conditions)
        return query

    async def get_app_conversation_info(
        self, conversation_id: UUID
    ) -> AppConversationInfo | None:
        query = self._secure_select().where(
            StoredAppConversationInfo.id == conversation_id
        )
        result_set = await self.session.execute(query)
        result = result_set.scalar_one_or_none()
        if result:
            return AppConversationInfo(**row2dict(result))
        return None

    async def batch_get_app_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversationInfo | None]:
        query = self._secure_select().where(
            StoredAppConversationInfo.id.in_(conversation_ids)
        )
        rows = await self.session.execute(query)
        info_by_id = {info.id: info for info in rows}
        results: list[AppConversationInfo | None] = []
        for conversation_id in conversation_ids:
            info = info_by_id.get(conversation_id)
            if info:
                results.append(AppConversationInfo(**row2dict(info)))
            else:
                results.append(None)

        return results

    async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        if self.user_id:
            query = select(StoredAppConversationInfo).where(StoredAppConversationInfo.id == info.id)
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            assert existing is None or existing.created_by_user_id == self.user_id
        await self.session.merge(StoredAppConversationInfo(**info.model_dump()))
        await self.session.commit()
        return info

    def _secure_select(self):
        query = select(StoredAppConversationInfo)
        if self.user_id:
            query = query.where(StoredAppConversationInfo.created_by_user_id == self.user_id)
        return query


class SQLAppConversationServiceManager(AppConversationInfoServiceManager):
    def get_unsecured_resolver(self) -> Callable:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import db_service

        def resolve_app_conversation_service(
            session: AsyncSession = Depends(db_service().managed_session_dependency),
        ) -> AppConversationInfoService:
            return SQLAppConversationInfoService(session=session)

        return resolve_app_conversation_service

    def get_resolver_for_current_user(self) -> Callable:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import db_service, user_manager

        async def resolve_app_conversation_service(
            user_service: UserService = Depends(user_manager().get_resolver_for_current_user()),
            session: AsyncSession = Depends(db_service().managed_session_dependency),
        ) -> AppConversationInfoService:
            user_id = await user_service.get_user_id()
            service = SQLAppConversationInfoService(session=session, user_id=user_id)
            return service

        return resolve_app_conversation_service
