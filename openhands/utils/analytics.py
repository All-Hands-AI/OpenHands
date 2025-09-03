"""Analytics utilities for tracking events with PostHog."""

import os
from typing import Any, Optional

from openhands.core.logger import openhands_logger as logger

try:
    import posthog

    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False
    logger.warning('PostHog not available. Analytics tracking will be disabled.')


class AnalyticsClient:
    """Client for tracking analytics events with PostHog."""

    def __init__(self):
        """Initialize the analytics client."""
        self._client = None
        self._enabled = False

        if POSTHOG_AVAILABLE:
            # Get PostHog configuration from environment or server config
            api_key = os.environ.get(
                'POSTHOG_API_KEY', 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
            )
            host = os.environ.get('POSTHOG_HOST', 'https://us.i.posthog.com')

            if api_key:
                try:
                    posthog.api_key = api_key
                    posthog.host = host
                    self._client = posthog
                    self._enabled = True
                    logger.debug('PostHog analytics client initialized successfully')
                except Exception as e:
                    logger.error(f'Failed to initialize PostHog client: {e}')
                    self._enabled = False
            else:
                logger.warning(
                    'PostHog API key not found. Analytics tracking disabled.'
                )
        else:
            logger.info('PostHog not available. Analytics tracking disabled.')

    def track(
        self, user_id: str, event: str, properties: Optional[dict[str, Any]] = None
    ) -> None:
        """Track an analytics event.

        Args:
            user_id: Unique identifier for the user
            event: Name of the event to track
            properties: Optional dictionary of event properties
        """
        if not self._enabled or not self._client:
            logger.debug(f'Analytics tracking disabled. Would track: {event}')
            return

        try:
            # Ensure properties is a dictionary
            if properties is None:
                properties = {}

            # Add common properties
            properties.update({'source': 'openhands', 'component': 'tom_agent'})

            self._client.capture(
                distinct_id=user_id, event=event, properties=properties
            )
            logger.debug(f'Tracked event: {event} for user: {user_id}')

        except Exception as e:
            logger.error(f'Failed to track event {event}: {e}')

    def identify(
        self, user_id: str, properties: Optional[dict[str, Any]] = None
    ) -> None:
        """Identify a user with properties.

        Args:
            user_id: Unique identifier for the user
            properties: Optional dictionary of user properties
        """
        if not self._enabled or not self._client:
            logger.debug(f'Analytics tracking disabled. Would identify user: {user_id}')
            return

        try:
            if properties is None:
                properties = {}

            self._client.identify(distinct_id=user_id, properties=properties)
            logger.debug(f'Identified user: {user_id}')

        except Exception as e:
            logger.error(f'Failed to identify user {user_id}: {e}')

    def flush(self) -> None:
        """Flush any pending events."""
        if self._enabled and self._client:
            try:
                self._client.flush()
                logger.debug('Flushed analytics events')
            except Exception as e:
                logger.error(f'Failed to flush analytics events: {e}')


# Global analytics client instance
_analytics_client: Optional[AnalyticsClient] = None


def get_analytics_client() -> AnalyticsClient:
    """Get the global analytics client instance."""
    global _analytics_client
    if _analytics_client is None:
        _analytics_client = AnalyticsClient()
    return _analytics_client


def track_tom_event(
    user_id: str, event: str, properties: Optional[dict[str, Any]] = None
) -> None:
    """Convenience function to track ToM agent events.

    Args:
        user_id: Unique identifier for the user
        event: Name of the event to track
        properties: Optional dictionary of event properties
    """
    client = get_analytics_client()
    client.track(user_id, event, properties)
