"""Unit tests for PostHog tracking utilities."""

from unittest.mock import MagicMock, patch

import pytest

from openhands.utils.posthog_tracker import track_agent_task_completed


@pytest.fixture
def mock_posthog():
    """Mock the posthog module."""
    with patch('openhands.utils.posthog_tracker.posthog') as mock_ph:
        mock_ph.capture = MagicMock()
        yield mock_ph


def test_track_agent_task_completed_with_user_id(mock_posthog):
    """Test tracking agent task completion with user ID."""
    # Initialize posthog manually in the test
    import openhands.utils.posthog_tracker as tracker

    tracker.posthog = mock_posthog

    track_agent_task_completed(
        conversation_id='test-conversation-123',
        user_id='user-456',
        app_mode='saas',
    )

    mock_posthog.capture.assert_called_once_with(
        distinct_id='user-456',
        event='agent_task_completed',
        properties={
            'conversation_id': 'test-conversation-123',
            'user_id': 'user-456',
            'app_mode': 'saas',
        },
    )


def test_track_agent_task_completed_without_user_id(mock_posthog):
    """Test tracking agent task completion without user ID (anonymous)."""
    import openhands.utils.posthog_tracker as tracker

    tracker.posthog = mock_posthog

    track_agent_task_completed(
        conversation_id='test-conversation-789',
        user_id=None,
        app_mode='oss',
    )

    mock_posthog.capture.assert_called_once_with(
        distinct_id='conversation_test-conversation-789',
        event='agent_task_completed',
        properties={
            'conversation_id': 'test-conversation-789',
            'user_id': None,
            'app_mode': 'oss',
        },
    )


def test_track_agent_task_completed_default_app_mode(mock_posthog):
    """Test tracking with default app_mode."""
    import openhands.utils.posthog_tracker as tracker

    tracker.posthog = mock_posthog

    track_agent_task_completed(
        conversation_id='test-conversation-999',
        user_id='user-111',
    )

    mock_posthog.capture.assert_called_once_with(
        distinct_id='user-111',
        event='agent_task_completed',
        properties={
            'conversation_id': 'test-conversation-999',
            'user_id': 'user-111',
            'app_mode': 'unknown',
        },
    )


def test_track_agent_task_completed_handles_errors(mock_posthog):
    """Test that tracking errors are handled gracefully."""
    import openhands.utils.posthog_tracker as tracker

    tracker.posthog = mock_posthog
    mock_posthog.capture.side_effect = Exception('PostHog API error')

    # Should not raise an exception
    track_agent_task_completed(
        conversation_id='test-conversation-error',
        user_id='user-error',
        app_mode='saas',
    )


def test_track_agent_task_completed_when_posthog_not_installed():
    """Test tracking when posthog is not installed."""
    import openhands.utils.posthog_tracker as tracker

    # Simulate posthog not being installed
    tracker.posthog = None

    # Should not raise an exception
    track_agent_task_completed(
        conversation_id='test-conversation-no-ph',
        user_id='user-no-ph',
        app_mode='oss',
    )
