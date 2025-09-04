import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

# Mock the modules that are causing issues
sys.modules['google'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.sql'] = MagicMock()
sys.modules['google.cloud.sql.connector'] = MagicMock()
sys.modules['google.cloud.sql.connector.Connector'] = MagicMock()
mock_db_module = MagicMock()
mock_db_module.a_session_maker = MagicMock()
sys.modules['storage.database'] = mock_db_module

# Now import the modules we need
from server.routes.feedback import (  # noqa: E402
    FeedbackRequest,
    submit_conversation_feedback,
)
from storage.feedback import ConversationFeedback  # noqa: E402


@pytest.mark.asyncio
async def test_submit_feedback():
    """Test submitting feedback for a conversation."""
    # Create a mock database session
    mock_session = MagicMock()

    # Test data
    feedback_data = FeedbackRequest(
        conversation_id='test-conversation-123',
        event_id=42,
        rating=5,
        reason='The agent was very helpful',
        metadata={'browser': 'Chrome', 'os': 'Windows'},
    )

    # Mock session_maker and call_sync_from_async
    with patch('server.routes.feedback.session_maker') as mock_session_maker, patch(
        'server.routes.feedback.call_sync_from_async'
    ) as mock_call_sync:
        mock_session_maker.return_value.__enter__.return_value = mock_session
        mock_session_maker.return_value.__exit__.return_value = None

        # Mock call_sync_from_async to execute the function
        def mock_call_sync_side_effect(func):
            return func()

        mock_call_sync.side_effect = mock_call_sync_side_effect

        # Call the function
        result = await submit_conversation_feedback(feedback_data)

        # Check response
        assert result == {
            'status': 'success',
            'message': 'Feedback submitted successfully',
        }

        # Verify the database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify the correct data was passed to add
        added_feedback = mock_session.add.call_args[0][0]
        assert isinstance(added_feedback, ConversationFeedback)
        assert added_feedback.conversation_id == 'test-conversation-123'
        assert added_feedback.event_id == 42
        assert added_feedback.rating == 5
        assert added_feedback.reason == 'The agent was very helpful'
        assert added_feedback.metadata == {'browser': 'Chrome', 'os': 'Windows'}


@pytest.mark.asyncio
async def test_invalid_rating():
    """Test submitting feedback with an invalid rating."""
    # Create a mock database session
    mock_session = MagicMock()

    # Since Pydantic validation happens before our function is called,
    # we need to patch the validation to test our function's validation
    with patch(
        'server.routes.feedback.FeedbackRequest.model_validate'
    ) as mock_validate:
        # Create a feedback object with an invalid rating
        feedback_data = MagicMock()
        feedback_data.conversation_id = 'test-conversation-123'
        feedback_data.rating = 6  # Invalid rating
        feedback_data.reason = 'The agent was very helpful'
        feedback_data.event_id = None
        feedback_data.metadata = None

        # Mock the validation to return our object
        mock_validate.return_value = feedback_data

        # Mock session_maker and call_sync_from_async
        with patch('server.routes.feedback.session_maker') as mock_session_maker, patch(
            'server.routes.feedback.call_sync_from_async'
        ) as mock_call_sync:
            mock_session_maker.return_value.__enter__.return_value = mock_session
            mock_session_maker.return_value.__exit__.return_value = None
            mock_call_sync.return_value = None

            # Call the function and expect an exception
            with pytest.raises(HTTPException) as excinfo:
                await submit_conversation_feedback(feedback_data)

            # Check the exception details
            assert excinfo.value.status_code == 400
            assert 'Rating must be between 1 and 5' in excinfo.value.detail

            # Verify no database operations were called
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()
