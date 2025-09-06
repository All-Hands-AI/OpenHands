"""Simplified analytics utilities for tracking events with PostHog."""

import socket
from typing import Any, Optional

import posthog

from openhands.core.logger import openhands_logger as logger
from openhands.server.config.server_config import load_server_config

server_config = load_server_config()
posthog.api_key = server_config.posthog_client_key
posthog.host = 'https://us.i.posthog.com'
logger.debug('PostHog initialized successfully')


def get_anonymous_user_id() -> str:
    """Generate anonymous user ID from machine info."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        combined = f'{local_ip}_{hostname}'
        return combined
    except Exception as e:
        logger.error(f'Failed to generate anonymous user ID: {e}')
        return 'unknown_user'


def track_tom_event(event: str, properties: Optional[dict[str, Any]] = None) -> None:
    """Track ToM agent events with PostHog.

    Args:
        user_id: User identifier (will be replaced with anonymous ID)
        event: Name of the event to track
        properties: Optional dictionary of event properties
    """

    try:
        # Use anonymous user ID for privacy
        anonymous_id = get_anonymous_user_id()

        # Ensure properties is a dictionary
        if properties is None:
            properties = {}

        # Add common properties
        properties.update({'source': 'openhands_cli', 'component': 'tom_agent'})

        posthog.capture(distinct_id=anonymous_id, event=event, properties=properties)
        logger.debug(f'Tracked event: {event} for anonymous user: {anonymous_id}')

    except Exception as e:
        logger.error(f'Failed to track event {event}: {e}')
