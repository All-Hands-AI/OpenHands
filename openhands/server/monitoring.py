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

    @classmethod
    def get_instance(
        cls,
        config: AppConfig,
    ) -> 'MonitoringListener':
        return cls()
