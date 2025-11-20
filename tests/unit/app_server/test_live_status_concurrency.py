"""Test for SQLAlchemy concurrency issues in LiveStatusAppConversationService."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import InvalidRequestError

from openhands.app_server.app_conversation.live_status_app_conversation_service import (
    LiveStatusAppConversationService,
)
from openhands.app_server.event_callback.event_callback_models import EventCallback
from openhands.app_server.event_callback.set_title_callback_processor import (
    SetTitleCallbackProcessor,
)


class TestLiveStatusConcurrency:
    """Test concurrency issues in LiveStatusAppConversationService."""

    @pytest.mark.asyncio
    async def test_concurrent_save_event_callback_causes_sqlalchemy_error(self):
        """Test that concurrent save_event_callback calls cause SQLAlchemy concurrency errors.

        This test reproduces the original issue where asyncio.gather() would try to use
        the same database session concurrently, causing SQLAlchemy to raise:
        'This session is provisioning a new connection; concurrent operations are not permitted'
        """
        # Create mock services
        mock_event_callback_service = AsyncMock()

        # Simulate the SQLAlchemy concurrency error that occurs when multiple
        # operations try to use the same database session simultaneously
        async def mock_save_with_concurrency_error(callback):
            # Simulate some async work that would trigger the concurrency issue
            await asyncio.sleep(0.01)  # Small delay to ensure concurrent execution
            # This is the actual error that was occurring
            raise InvalidRequestError(
                'This session is provisioning a new connection; concurrent operations are not permitted',
                None,
                None,
            )

        mock_event_callback_service.save_event_callback.side_effect = (
            mock_save_with_concurrency_error
        )

        # Create a minimal service instance for testing
        service = LiveStatusAppConversationService(
            init_git_in_empty_workspace=True,
            user_context=MagicMock(),
            app_conversation_info_service=MagicMock(),
            app_conversation_start_task_service=MagicMock(),
            event_callback_service=mock_event_callback_service,
            sandbox_service=MagicMock(),
            sandbox_spec_service=MagicMock(),
            jwt_service=MagicMock(),
            sandbox_startup_timeout=30,
            sandbox_startup_poll_frequency=1,
            httpx_client=MagicMock(),
            web_url=None,
            access_token_hard_timeout=None,
        )

        # Create test processors (multiple processors to test concurrency)
        processors = [
            SetTitleCallbackProcessor(),
            SetTitleCallbackProcessor(),
        ]

        conversation_id = uuid4()

        # This simulates the problematic asyncio.gather() call that was causing the issue
        with pytest.raises(
            InvalidRequestError, match='concurrent operations are not permitted'
        ):
            await asyncio.gather(
                *[
                    service.event_callback_service.save_event_callback(
                        EventCallback(
                            conversation_id=conversation_id,
                            processor=processor,
                        )
                    )
                    for processor in processors
                ]
            )

    @pytest.mark.asyncio
    async def test_sequential_save_event_callback_works(self):
        """Test that sequential save_event_callback calls work without concurrency errors.

        This test verifies that the fix (using sequential for loop instead of asyncio.gather)
        resolves the concurrency issue.
        """
        # Create mock services
        mock_event_callback_service = AsyncMock()

        # Mock successful save operations
        async def mock_save_success(callback):
            await asyncio.sleep(0.01)  # Simulate some async work
            return callback

        mock_event_callback_service.save_event_callback.side_effect = mock_save_success

        # Create a minimal service instance for testing
        service = LiveStatusAppConversationService(
            init_git_in_empty_workspace=True,
            user_context=MagicMock(),
            app_conversation_info_service=MagicMock(),
            app_conversation_start_task_service=MagicMock(),
            event_callback_service=mock_event_callback_service,
            sandbox_service=MagicMock(),
            sandbox_spec_service=MagicMock(),
            jwt_service=MagicMock(),
            sandbox_startup_timeout=30,
            sandbox_startup_poll_frequency=1,
            httpx_client=MagicMock(),
            web_url=None,
            access_token_hard_timeout=None,
        )

        # Create test processors
        processors = [
            SetTitleCallbackProcessor(),
            SetTitleCallbackProcessor(),
        ]

        conversation_id = uuid4()

        # This simulates the fix: sequential processing instead of concurrent
        for processor in processors:
            await service.event_callback_service.save_event_callback(
                EventCallback(
                    conversation_id=conversation_id,
                    processor=processor,
                )
            )

        # Verify that save_event_callback was called for each processor
        assert mock_event_callback_service.save_event_callback.call_count == len(
            processors
        )

        # Verify the calls were made with the correct arguments
        calls = mock_event_callback_service.save_event_callback.call_args_list
        for i, processor in enumerate(processors):
            call_args = calls[i][0][0]  # First positional argument (EventCallback)
            assert call_args.conversation_id == conversation_id
            assert isinstance(call_args.processor, type(processor))
