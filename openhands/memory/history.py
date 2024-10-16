from openhands.events.event import Event
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.stream import EventStream


class ShortTermHistory(list[Event]):
    """A list of events that represents the short-term memory of the agent.

    This class provides methods to retrieve and filter the events in the history of the running agent from the event stream.
    """

    start_id: int
    end_id: int
    _event_stream: EventStream
    delegates: dict[tuple[int, int], tuple[str, str]]

    def __init__(self):
        super().__init__()
        self.start_id = -1
        self.end_id = -1
        self.delegates = {}

    def set_event_stream(self, event_stream: EventStream):
        self._event_stream = event_stream

    def has_delegation(self) -> bool:
        for event in self._event_stream.get_events():
            if isinstance(event, AgentDelegateObservation):
                return True
        return False
