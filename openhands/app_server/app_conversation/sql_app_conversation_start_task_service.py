# pyright: reportArgumentType=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
"""SQL implementation of AppConversationStartTaskService.

This implementation provides CRUD operations for conversation start tasks focused purely
on SQL operations:
- Direct database access without permission checks
- Batch operations for efficient data retrieval
- Full async/await support using SQL async sessions

Security and permission checks are handled by wrapper services.

Key components:
- SQLAppConversationStartTaskService: Main service class implementing all operations
- SQLAppConversationStartTaskServiceManager: Dependency injection resolver for FastAPI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.agent_server.models import utc_now
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationStartTask,
)
from openhands.app_server.app_conversation.app_conversation_start_task_service import (
    AppConversationStartTaskService,
    AppConversationStartTaskServiceManager,
)
from openhands.app_server.user.user_service import UserService

logger = logging.getLogger(__name__)


@dataclass
class SQLAppConversationStartTaskService(AppConversationStartTaskService):
    """SQL implementation of AppConversationStartTaskService focused on db operations.

    This allows storing and retrieving conversation start tasks from the database."""

    session: AsyncSession
    user_id: str | None = None

    async def batch_get_app_conversation_start_tasks(
        self, task_ids: list[UUID]
    ) -> list[AppConversationStartTask | None]:
        """Get a batch of start tasks, return None for any missing."""
        if not task_ids:
            return []

        query = select(AppConversationStartTask).where(
            AppConversationStartTask.id.in_(task_ids)  # type: ignore
        )
        if self.user_id:
            query = query.where(
                AppConversationStartTask.created_by_user_id == self.user_id
            )

        result = await self.session.execute(query)
        tasks_by_id = {task.id: task for task in result.scalars().all()}

        # Return tasks in the same order as requested, with None for missing ones
        return [tasks_by_id.get(task_id) for task_id in task_ids]

    async def get_app_conversation_start_task(
        self, task_id: UUID
    ) -> AppConversationStartTask | None:
        """Get a single start task, returning None if missing."""
        query = select(AppConversationStartTask).where(
            AppConversationStartTask.id == task_id
        )
        if self.user_id:
            query = query.where(
                AppConversationStartTask.created_by_user_id == self.user_id
            )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_app_conversation_start_task(
        self, task: AppConversationStartTask
    ) -> AppConversationStartTask:
        if self.user_id:
            query = select(AppConversationStartTask).where(
                AppConversationStartTask.id == task.id
            )
            result = await self.session.execute(query)
            existing: AppConversationStartTask = result.scalar_one_or_none()
            assert existing is None or existing.created_by_user_id == self.user_id
        task.updated_at = utc_now()
        await self.session.merge(task)
        await self.session.commit()
        return task


class SQLAppConversationStartTaskServiceManager(AppConversationStartTaskServiceManager):
    def get_unsecured_resolver(self) -> Callable:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import db_service

        # Create dependency at module level to avoid B008
        _db_dependency = Depends(db_service().managed_session_dependency)

        def resolve_app_conversation_start_task_service(
            session: AsyncSession = _db_dependency,
        ) -> AppConversationStartTaskService:
            return SQLAppConversationStartTaskService(session=session)

        return resolve_app_conversation_start_task_service

    def get_resolver_for_current_user(self) -> Callable:
        # Define inline to prevent circular lookup
        from openhands.app_server.config import db_service, user_manager

        # Create dependencies at module level to avoid B008
        _user_dependency = Depends(user_manager().get_resolver_for_current_user())
        _db_dependency = Depends(db_service().managed_session_dependency)

        async def resolve_app_conversation_start_task_service(
            user_service: UserService = _user_dependency,
            session: AsyncSession = _db_dependency,
        ) -> AppConversationStartTaskService:
            user_id = await user_service.get_user_id()
            service = SQLAppConversationStartTaskService(
                session=session, user_id=user_id
            )
            return service

        return resolve_app_conversation_start_task_service
