# pyright: reportArgumentType=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
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
- SQLAppConversationServiceResolver: Dependency injection resolver for FastAPI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
    AppConversationInfoServiceResolver,
)
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
    AppConversationInfoPage,
    AppConversationSortOrder,
)
from openhands.app_server.database import managed_session_dependency
from openhands.app_server.errors import AuthError
from openhands.app_server.user.user_service import UserService

logger = logging.getLogger(__name__)


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
        query = select(AppConversationInfo)

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
            query = query.order_by(AppConversationInfo.created_at)
        elif sort_order == AppConversationSortOrder.CREATED_AT_DESC:
            query = query.order_by(AppConversationInfo.created_at.desc())  # type: ignore
        elif sort_order == AppConversationSortOrder.UPDATED_AT:
            query = query.order_by(AppConversationInfo.updated_at)
        elif sort_order == AppConversationSortOrder.UPDATED_AT_DESC:
            query = query.order_by(AppConversationInfo.updated_at.desc())  # type: ignore
        elif sort_order == AppConversationSortOrder.TITLE:
            query = query.order_by(AppConversationInfo.title)
        elif sort_order == AppConversationSortOrder.TITLE:
            query = query.order_by(AppConversationInfo.title.desc())  # type: ignore

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

        # Apply sorting (default to created_at desc)
        query = query.order_by(AppConversationInfo.created_at.desc())  # type: ignore

        # Apply limit and get one extra to check if there are more results
        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        # Check if there are more results
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

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
        query = select(func.count(AppConversationInfo.id))

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
                AppConversationInfo.title.like(f'%{title__contains}%')  # type: ignore
            )

        if created_at__gte is not None:
            conditions.append(AppConversationInfo.created_at >= created_at__gte)  # type: ignore

        if created_at__lt is not None:
            conditions.append(AppConversationInfo.created_at < created_at__lt)  # type: ignore

        if updated_at__gte is not None:
            conditions.append(AppConversationInfo.updated_at >= updated_at__gte)  # type: ignore

        if updated_at__lt is not None:
            conditions.append(AppConversationInfo.updated_at < updated_at__lt)  # type: ignore

        if conditions:
            query = query.where(*conditions)
        return query

    async def get_app_conversation_info(
        self, conversation_id: UUID
    ) -> AppConversationInfo | None:
        query = select(AppConversationInfo).where(
            AppConversationInfo.id == conversation_id
        )
        result_set = await self.session.execute(query)
        result = result_set.scalar_one_or_none()
        return result

    async def batch_get_app_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversationInfo | None]:
        query = select(AppConversationInfo).where(
            AppConversationInfo.id.in_(conversation_ids)  # type: ignore
        )
        rows = await self.session.execute(query)
        info_by_id = {info.id: info for info in rows}
        results = [
            info_by_id.get(conversation_id) for conversation_id in conversation_ids
        ]
        return results

    async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        self.session.add(info)
        await self.session.commit()
        await self.session.refresh(info)
        return info


class SQLAppConversationServiceResolver(AppConversationInfoServiceResolver):
    def get_unsecured_resolver(self) -> Callable:
        # Define inline to prevent circular lookup
        def resolve_app_conversation_service(
            session: AsyncSession = Depends(managed_session_dependency),
        ) -> AppConversationInfoService:
            return SQLAppConversationInfoService(session=session)

        return resolve_app_conversation_service

    def get_resolver_for_user(self) -> Callable:
        # Define inline to prevent circular lookup

        from openhands.app_server.dependency import get_dependency_resolver

        user_service_resolver = get_dependency_resolver().user.get_resolver_for_user()

        def resolve_app_conversation_service(
            user_service: UserService = Depends(user_service_resolver),
            session: AsyncSession = Depends(managed_session_dependency),
        ) -> AppConversationInfoService:
            current_user = user_service.get_current_user()
            if current_user is None:
                raise AuthError('Not logged in!')
            service = SQLAppConversationInfoService(session=session)
            return service

        return resolve_app_conversation_service
