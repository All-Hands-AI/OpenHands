from openhands.core.config.app_config import AppConfig
from openhands.events.event import Event


class MonitoringListener:
    """
    Allow tracking of application activity for monitoring purposes.

    Implementations should be non-disruptive, do not raise or block to perform I/O.
    """

    def on_session_event(self, event: Event) -> None:
        """
        Track metrics about events being added to a Session's EventStream.
        """
        pass

    def on_conversation_start(self, duration: float) -> None:
        """
        Track a successful conversation start.
        Duration is start time in seconds observed by AgentSession.
        """
        pass

    @classmethod
    def get_instance(
        cls,
        config: AppConfig,
    ) -> 'MonitoringListener':
        return cls()
