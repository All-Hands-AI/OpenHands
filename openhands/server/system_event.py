from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any


class SystemEventType(StrEnum):
    CONVERSATION_START = 'conversation_start'
    AGENT_STATUS_ERROR = 'agent_status_error'


class SystemEventListener(ABC):
    @abstractmethod
    def on_event(self, type: SystemEventType, data: dict[str, Any]):
        """
        Implementations override this to track events for their metrics.
        This is expected to be non-blocking (fast).
        Exceptions raised will be swallowed.
        """
        pass


class SystemEventHandler:
    _listeners: list[SystemEventListener]

    def __init__(self):
        self._listeners = []

    def add_listener(self, listener: SystemEventListener):
        """Forward future on_event calls to listener."""
        self._listeners.append(listener)

    def on_event(self, type: SystemEventType, session_id: str, **kwargs):
        """Forwards on_event calls to all listeners, swallowing exceptions."""
        for listener in self._listeners:
            try:
                event_data = {'session_id': session_id, **kwargs}
                listener.on_event(type, event_data)
            except Exception as _:
                pass
