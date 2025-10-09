"""Tests for SQLAppConversationStartTaskService.

This module tests the SQL implementation of AppConversationStartTaskService,
focusing on basic CRUD operations and batch operations using SQLite as a mock database.
"""

from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationStartRequest,
    AppConversationStartTask,
    AppConversationStartTaskStatus,
)
from openhands.app_server.app_conversation.sql_app_conversation_start_task_service import (
    SQLAppConversationStartTaskService,
)
from openhands.app_server.utils.sql_utils import Base


@pytest.fixture
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def service(async_session: AsyncSession) -> SQLAppConversationStartTaskService:
    """Create a SQLAppConversationStartTaskService instance for testing."""
    return SQLAppConversationStartTaskService(session=async_session)


@pytest.fixture
def sample_request() -> AppConversationStartRequest:
    """Create a sample AppConversationStartRequest for testing."""
    return AppConversationStartRequest(
        agent='CodeActAgent',
        language='en',
        args={},
        confirmation_mode=False,
        security_analyzer='',
        microagent_names=[],
        runtime='local',
        file_uploads=[],
        selected_repository=None,
    )


@pytest.fixture
def sample_task(
    sample_request: AppConversationStartRequest,
) -> AppConversationStartTask:
    """Create a sample AppConversationStartTask for testing."""
    return AppConversationStartTask(
        id=uuid4(),
        created_by_user_id='test_user',
        status=AppConversationStartTaskStatus.WORKING,
        detail=None,
        app_conversation_id=None,
        sandbox_id=None,
        agent_server_url=None,
        request=sample_request,
    )


class TestSQLAppConversationStartTaskService:
    """Test cases for SQLAppConversationStartTaskService."""

    async def test_save_and_get_task(
        self,
        service: SQLAppConversationStartTaskService,
        sample_task: AppConversationStartTask,
    ):
        """Test saving and retrieving a single task."""
        # Save the task
        saved_task = await service.save_app_conversation_start_task(sample_task)

        # Verify the task was saved correctly
        assert saved_task.id == sample_task.id
        assert saved_task.created_by_user_id == sample_task.created_by_user_id
        assert saved_task.status == sample_task.status
        assert saved_task.request == sample_task.request

        # Retrieve the task
        retrieved_task = await service.get_app_conversation_start_task(sample_task.id)

        # Verify the retrieved task matches
        assert retrieved_task is not None
        assert retrieved_task.id == sample_task.id
        assert retrieved_task.created_by_user_id == sample_task.created_by_user_id
        assert retrieved_task.status == sample_task.status
        assert retrieved_task.request == sample_task.request

    async def test_get_nonexistent_task(
        self, service: SQLAppConversationStartTaskService
    ):
        """Test retrieving a task that doesn't exist."""
        nonexistent_id = uuid4()
        result = await service.get_app_conversation_start_task(nonexistent_id)
        assert result is None

    async def test_batch_get_tasks(
        self,
        service: SQLAppConversationStartTaskService,
        sample_request: AppConversationStartRequest,
    ):
        """Test batch retrieval of tasks."""
        # Create multiple tasks
        task1 = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user1',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )
        task2 = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user2',
            status=AppConversationStartTaskStatus.READY,
            request=sample_request,
        )
        task3 = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user3',
            status=AppConversationStartTaskStatus.ERROR,
            request=sample_request,
        )

        # Save all tasks
        await service.save_app_conversation_start_task(task1)
        await service.save_app_conversation_start_task(task2)
        await service.save_app_conversation_start_task(task3)

        # Test batch retrieval with all existing IDs
        task_ids = [task1.id, task2.id, task3.id]
        retrieved_tasks = await service.batch_get_app_conversation_start_tasks(task_ids)

        assert len(retrieved_tasks) == 3
        assert all(task is not None for task in retrieved_tasks)

        # Verify order is preserved
        assert retrieved_tasks[0].id == task1.id
        assert retrieved_tasks[1].id == task2.id
        assert retrieved_tasks[2].id == task3.id

    async def test_batch_get_tasks_with_missing(
        self,
        service: SQLAppConversationStartTaskService,
        sample_task: AppConversationStartTask,
    ):
        """Test batch retrieval with some missing tasks."""
        # Save one task
        await service.save_app_conversation_start_task(sample_task)

        # Request batch with existing and non-existing IDs
        nonexistent_id = uuid4()
        task_ids = [sample_task.id, nonexistent_id]
        retrieved_tasks = await service.batch_get_app_conversation_start_tasks(task_ids)

        assert len(retrieved_tasks) == 2
        assert retrieved_tasks[0] is not None
        assert retrieved_tasks[0].id == sample_task.id
        assert retrieved_tasks[1] is None

    async def test_batch_get_empty_list(
        self, service: SQLAppConversationStartTaskService
    ):
        """Test batch retrieval with empty list."""
        result = await service.batch_get_app_conversation_start_tasks([])
        assert result == []

    async def test_update_task_status(
        self,
        service: SQLAppConversationStartTaskService,
        sample_task: AppConversationStartTask,
    ):
        """Test updating a task's status."""
        # Save initial task
        await service.save_app_conversation_start_task(sample_task)

        # Update the task status
        sample_task.status = AppConversationStartTaskStatus.READY
        sample_task.app_conversation_id = uuid4()
        sample_task.sandbox_id = 'test_sandbox'
        sample_task.agent_server_url = 'http://localhost:8000'

        # Save the updated task
        updated_task = await service.save_app_conversation_start_task(sample_task)

        # Verify the update
        assert updated_task.status == AppConversationStartTaskStatus.READY
        assert updated_task.app_conversation_id == sample_task.app_conversation_id
        assert updated_task.sandbox_id == 'test_sandbox'
        assert updated_task.agent_server_url == 'http://localhost:8000'

        # Retrieve and verify persistence
        retrieved_task = await service.get_app_conversation_start_task(sample_task.id)
        assert retrieved_task is not None
        assert retrieved_task.status == AppConversationStartTaskStatus.READY
        assert retrieved_task.app_conversation_id == sample_task.app_conversation_id

    async def test_user_isolation(
        self,
        async_session: AsyncSession,
        sample_request: AppConversationStartRequest,
    ):
        """Test that users can only access their own tasks."""
        # Create services for different users
        user1_service = SQLAppConversationStartTaskService(
            session=async_session, user_id='user1'
        )
        user2_service = SQLAppConversationStartTaskService(
            session=async_session, user_id='user2'
        )

        # Create tasks for different users
        user1_task = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user1',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )
        user2_task = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user2',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )

        # Save tasks using respective services
        await user1_service.save_app_conversation_start_task(user1_task)
        await user2_service.save_app_conversation_start_task(user2_task)

        # Test that user1 can only access their task
        user1_retrieved = await user1_service.get_app_conversation_start_task(
            user1_task.id
        )
        user1_cannot_access = await user1_service.get_app_conversation_start_task(
            user2_task.id
        )

        assert user1_retrieved is not None
        assert user1_retrieved.id == user1_task.id
        assert user1_cannot_access is None

        # Test that user2 can only access their task
        user2_retrieved = await user2_service.get_app_conversation_start_task(
            user2_task.id
        )
        user2_cannot_access = await user2_service.get_app_conversation_start_task(
            user1_task.id
        )

        assert user2_retrieved is not None
        assert user2_retrieved.id == user2_task.id
        assert user2_cannot_access is None

    async def test_batch_get_with_user_isolation(
        self,
        async_session: AsyncSession,
        sample_request: AppConversationStartRequest,
    ):
        """Test batch retrieval with user isolation."""
        # Create services for different users
        user1_service = SQLAppConversationStartTaskService(
            session=async_session, user_id='user1'
        )
        user2_service = SQLAppConversationStartTaskService(
            session=async_session, user_id='user2'
        )

        # Create tasks for different users
        user1_task = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user1',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )
        user2_task = AppConversationStartTask(
            id=uuid4(),
            created_by_user_id='user2',
            status=AppConversationStartTaskStatus.WORKING,
            request=sample_request,
        )

        # Save tasks
        await user1_service.save_app_conversation_start_task(user1_task)
        await user2_service.save_app_conversation_start_task(user2_task)

        # Test batch retrieval with user isolation
        task_ids = [user1_task.id, user2_task.id]
        user1_results = await user1_service.batch_get_app_conversation_start_tasks(
            task_ids
        )

        # User1 should only see their task, user2's task should be None
        assert len(user1_results) == 2
        assert user1_results[0] is not None
        assert user1_results[0].id == user1_task.id
        assert user1_results[1] is None

    async def test_task_timestamps(
        self,
        service: SQLAppConversationStartTaskService,
        sample_task: AppConversationStartTask,
    ):
        """Test that timestamps are properly set and updated."""
        # Save initial task
        saved_task = await service.save_app_conversation_start_task(sample_task)

        # Verify timestamps are set
        assert saved_task.created_at is not None
        assert saved_task.updated_at is not None

        original_created_at = saved_task.created_at
        original_updated_at = saved_task.updated_at

        # Update the task
        saved_task.status = AppConversationStartTaskStatus.READY
        updated_task = await service.save_app_conversation_start_task(saved_task)

        # Verify created_at stays the same but updated_at changes
        assert updated_task.created_at == original_created_at
        assert updated_task.updated_at > original_updated_at
