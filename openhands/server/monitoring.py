from typing import Optional

from openhands.core.config.app_config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.server.analytics import UserAnalytics
from openhands.server.config.server_config import load_server_config


class MonitoringListener:
    """
    Allow tracking of application activity for monitoring purposes.

    Implementations should be non-disruptive, do not raise or block to perform I/O.
    """

    def __init__(self):
        """Initialize the MonitoringListener."""
        self.server_config = load_server_config()
        self.user_analytics = UserAnalytics.get_instance(self.server_config)

    def on_session_event(self, event: Event) -> None:
        """
        Track metrics about events being added to a Session's EventStream.
        """
        pass

    def on_agent_session_start(self, success: bool, duration: float) -> None:
        """
        Track an agent session start.
        Success is true if startup completed without error.
        Duration is start time in seconds observed by AgentSession.
        """
        pass

    def on_create_conversation(self) -> None:
        """
        Track the beginning of conversation creation.
        Does not currently capture whether it succeed.
        """
        pass

    def on_conversation_created(
        self,
        user_id: str,
        conversation_id: str,
        has_initial_message: bool = False,
        has_repository: bool = False,
        has_images: bool = False,
        user_consents_to_analytics: Optional[bool] = None,
    ) -> None:
        """
        Track when a new conversation is created.

        Args:
            user_id: The ID of the user
            conversation_id: The ID of the conversation
            has_initial_message: Whether the conversation was created with an initial message
            has_repository: Whether the conversation was created with a repository
            has_images: Whether the conversation was created with images
            user_consents_to_analytics: Whether the user has consented to analytics
        """
        # Only track if the user has explicitly consented to analytics
        if user_consents_to_analytics is True:
            try:
                self.user_analytics.track_conversation_created(
                    user_id,
                    conversation_id,
                    has_initial_message,
                    has_repository,
                    has_images,
                )
            except Exception as e:
                # Don't let analytics failures affect the application
                logger.error(f'Error tracking conversation creation: {e}')

    @classmethod
    def get_instance(
        cls,
        config: AppConfig,
    ) -> 'MonitoringListener':
        return cls()
