from __future__ import annotations

import os
from typing import Any, Dict, Optional

import posthog

from openhands.core.logger import openhands_logger as logger
from openhands.server.config.server_config import ServerConfig


class UserAnalytics:
    """
    Handles user analytics tracking using PostHog.
    Respects user opt-in settings for analytics.
    """

    _instance: Optional[UserAnalytics] = None

    def __init__(self, server_config: ServerConfig):
        """
        Initialize the UserAnalytics class.

        Args:
            server_config: The server configuration containing PostHog client key
        """
        self.posthog_client_key = server_config.posthog_client_key
        self.initialized = False
        self._initialize_posthog()

    def _initialize_posthog(self) -> None:
        """Initialize the PostHog client."""
        if not self.posthog_client_key:
            logger.warning('PostHog client key not found, analytics will be disabled')
            return

        try:
            # Initialize PostHog with the client key
            posthog_host = os.environ.get('POSTHOG_HOST', 'https://app.posthog.com')
            posthog.api_key = self.posthog_client_key
            posthog.host = posthog_host
            self.initialized = True
            logger.info('PostHog analytics initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize PostHog: {e}')
            self.initialized = False

    def track_event(
        self, user_id: str, event_name: str, properties: Dict[str, Any] | None = None
    ) -> bool:
        """
        Track an event in PostHog if the user has opted into analytics.

        Args:
            user_id: The ID of the user
            event_name: The name of the event to track
            properties: Additional properties to include with the event

        Returns:
            True if the event was tracked, False otherwise
        """
        if not self.initialized:
            return False

        if not user_id:
            logger.debug(f'Not tracking event {event_name}: No user ID provided')
            return False

        try:
            # Send the event to PostHog
            posthog.capture(
                distinct_id=user_id, event=event_name, properties=properties or {}
            )
            logger.debug(f'Tracked event {event_name} for user {user_id}')
            return True
        except Exception as e:
            logger.error(f'Failed to track event {event_name}: {e}')
            return False

    def track_conversation_created(
        self,
        user_id: str,
        conversation_id: str,
        has_initial_message: bool,
        has_repository: bool,
        has_images: bool,
    ) -> bool:
        """
        Track when a user creates a new conversation.

        Args:
            user_id: The ID of the user
            conversation_id: The ID of the conversation
            has_initial_message: Whether the conversation was created with an initial message
            has_repository: Whether the conversation was created with a repository
            has_images: Whether the conversation was created with images

        Returns:
            True if the event was tracked, False otherwise
        """
        properties = {
            'conversation_id': conversation_id,
            'has_initial_message': has_initial_message,
            'has_repository': has_repository,
            'has_images': has_images,
        }
        return self.track_event(user_id, 'conversation_created', properties)

    @classmethod
    def get_instance(cls, server_config: ServerConfig) -> UserAnalytics:
        """
        Get or create the singleton instance of UserAnalytics.

        Args:
            server_config: The server configuration

        Returns:
            The UserAnalytics instance
        """
        if cls._instance is None:
            cls._instance = UserAnalytics(server_config)
        return cls._instance
