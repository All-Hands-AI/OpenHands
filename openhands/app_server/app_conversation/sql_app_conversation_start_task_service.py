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
- SQLAppConversationStartTaskServiceResolver: Dependency injection resolver for FastAPI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from fastapi import Depends
from openhands.agent_server.models import utc_now
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationStartTask,
)
from openhands.app_server.app_conversation.app_conversation_start_task_service import (
    AppConversationStartTaskService,
    AppConversationStartTaskServiceResolver,
)

from openhands.app_server.database import async_session_dependency
from openhands.app_server.errors import AuthError
from openhands.app_server.user.user_service import UserService

logger = logging.getLogger(__name__)


@dataclass
class SQLAppConversationStartTaskService(AppConversationStartTaskService):
    """SQL implementation of AppConversationStartTaskService focused on db operations.

    This allows storing and retrieving conversation start tasks from the database."""

    session: AsyncSession

    async def batch_get_app_conversation_start_tasks(
        self, task_ids: list[UUID]
    ) -> list[AppConversationStartTask | None]:
        """Get a batch of start tasks, return None for any missing."""
        if not task_ids:
            return []

        query = select(AppConversationStartTask).where(
            AppConversationStartTask.id.in_(task_ids)  # type: ignore
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

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_app_conversation_start_task(
        self, task: AppConversationStartTask
    ) -> bool:
        """Store the start task object given.

        Return true if it was stored, false otherwise.
        """
        try:
            task.updated_at = utc_now()
            self.session.add(task)
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f'Failed to save conversation start task {task.id}: {e}')
            await self.session.rollback()
            return False


class SQLAppConversationStartTaskServiceResolver(
    AppConversationStartTaskServiceResolver
):
    def get_unsecured_resolver(self) -> Callable:
        # Define inline to prevent circular lookup
        def resolve_app_conversation_start_task_service(
            session: AsyncSession = Depends(self._get_async_session_dependency),
        ) -> AppConversationStartTaskService:
            return SQLAppConversationStartTaskService(session=session)

        return resolve_app_conversation_start_task_service

    def get_resolver_for_user(self) -> Callable:
        # Define inline to prevent circular lookup

        from openhands.app_server.dependency import get_dependency_resolver

        user_service_resolver = get_dependency_resolver().user.get_resolver_for_user()

        def resolve_app_conversation_start_task_service(
            user_service: UserService = Depends(user_service_resolver),
            session: AsyncSession = Depends(async_session_dependency),
        ) -> AppConversationStartTaskService:
            current_user = user_service.get_current_user()
            if current_user is None:
                raise AuthError('Not logged in!')
            service = SQLAppConversationStartTaskService(session=session)
            return service

        return resolve_app_conversation_start_task_service
