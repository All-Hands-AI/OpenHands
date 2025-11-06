"""PostHog tracking utilities for OpenHands events."""

import os

from openhands.core.logger import openhands_logger as logger

# Lazy import posthog to avoid import errors in environments where it's not installed
posthog = None


def _init_posthog():
    """Initialize PostHog client lazily."""
    global posthog
    if posthog is None:
        try:
            import posthog as ph

            posthog = ph
            posthog.api_key = os.environ.get(
                'POSTHOG_CLIENT_KEY', 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
            )
            posthog.host = os.environ.get('POSTHOG_HOST', 'https://us.i.posthog.com')
        except ImportError:
            logger.warning(
                'PostHog not installed. Analytics tracking will be disabled.'
            )
            posthog = None


def track_agent_task_completed(
    conversation_id: str,
    user_id: str | None = None,
    app_mode: str | None = None,
) -> None:
    """Track when an agent completes a task.

    Args:
        conversation_id: The ID of the conversation/session
        user_id: The ID of the user (optional, may be None for unauthenticated users)
        app_mode: The application mode (saas/oss), optional
    """
    _init_posthog()

    if posthog is None:
        return

    # Use conversation_id as distinct_id if user_id is not available
    # This ensures we can track completions even for anonymous users
    distinct_id = user_id if user_id else f'conversation_{conversation_id}'

    try:
        posthog.capture(
            distinct_id=distinct_id,
            event='agent_task_completed',
            properties={
                'conversation_id': conversation_id,
                'user_id': user_id,
                'app_mode': app_mode or 'unknown',
            },
        )
        logger.debug(
            'posthog_track',
            extra={
                'event': 'agent_task_completed',
                'conversation_id': conversation_id,
                'user_id': user_id,
            },
        )
    except Exception as e:
        logger.warning(
            f'Failed to track agent_task_completed to PostHog: {e}',
            extra={
                'conversation_id': conversation_id,
                'error': str(e),
            },
        )
