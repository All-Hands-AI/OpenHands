from typing import ClassVar, Iterable

from openhands.events.action.action import Action
from openhands.events.action.agent import (
    ChangeAgentStateAction,
)
from openhands.events.action.empty import NullAction
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.empty import NullObservation
from openhands.events.observation.observation import Observation
from openhands.events.stream import EventStream


class ShortTermHistory(list[Event]):
    """A list of events that represents the short-term memory of the agent.

    This class provides methods to retrieve and filter the events in the history of the running agent from the event stream.
    """

    start_id: int
    end_id: int
    _event_stream: EventStream
    delegates: dict[tuple[int, int], tuple[str, str]]
    filter_out: ClassVar[tuple[type[Event], ...]] = (
        NullAction,
        NullObservation,
        ChangeAgentStateAction,
        AgentStateChangedObservation,
    )

    def __init__(self):
        super().__init__()
        self.start_id = -1
        self.end_id = -1
        self.delegates = {}

    def set_event_stream(self, event_stream: EventStream):
        self._event_stream = event_stream

    def get_events_as_list(self, include_delegates: bool = False) -> list[Event]:
        """Return the history as a list of Event objects."""
        return list(self.get_events(include_delegates=include_delegates))

    def get_events(
        self,
        reverse: bool = False,
        include_delegates: bool = False,
        include_hidden=False,
    ) -> Iterable[Event]:
        """Return the events as a stream of Event objects."""
        # TODO handle AgentRejectAction, if it's not part of a chunk ending with an AgentDelegateObservation
        # or even if it is, because currently we don't add it to the summary

        # iterate from start_id to end_id, or reverse
        start_id = self.start_id if self.start_id != -1 else 0
        end_id = (
            self.end_id
            if self.end_id != -1
            else self._event_stream.get_latest_event_id()
        )

        for event in self._event_stream.get_events(
            start_id=start_id,
            end_id=end_id,
            reverse=reverse,
            filter_out_type=self.filter_out,
        ):
            if not include_hidden and hasattr(event, 'hidden') and event.hidden:
                continue
            # TODO add summaries
            # and filter out events that were included in a summary

            # filter out the events from a delegate of the current agent
            if not include_delegates and not any(
                # except for the delegate action and observation themselves, currently
                # AgentDelegateAction has id = delegate_start
                # AgentDelegateObservation has id = delegate_end
                delegate_start < event.id < delegate_end
                for delegate_start, delegate_end in self.delegates.keys()
            ):
                yield event
            elif include_delegates:
                yield event

    def get_last_action(self, end_id: int = -1) -> Action | None:
        """Return the last action from the event stream, filtered to exclude unwanted events."""
        # from end_id in reverse, find the first action
        end_id = self._event_stream.get_latest_event_id() if end_id == -1 else end_id

        last_action = next(
            (
                event
                for event in self._event_stream.get_events(
                    end_id=end_id, reverse=True, filter_out_type=self.filter_out
                )
                if isinstance(event, Action)
            ),
            None,
        )

        return last_action

    def get_last_observation(self, end_id: int = -1) -> Observation | None:
        """Return the last observation from the event stream, filtered to exclude unwanted events."""
        # from end_id in reverse, find the first observation
        end_id = self._event_stream.get_latest_event_id() if end_id == -1 else end_id

        last_observation = next(
            (
                event
                for event in self._event_stream.get_events(
                    end_id=end_id, reverse=True, filter_out_type=self.filter_out
                )
                if isinstance(event, Observation)
            ),
            None,
        )

        return last_observation

    def get_last_user_message(self) -> str:
        """Return the content of the last user message from the event stream."""
        last_user_message = next(
            (
                event.content
                for event in self._event_stream.get_events(reverse=True)
                if isinstance(event, MessageAction) and event.source == EventSource.USER
            ),
            None,
        )

        return last_user_message if last_user_message is not None else ''

    def get_last_agent_message(self) -> str:
        """Return the content of the last agent message from the event stream."""
        last_agent_message = next(
            (
                event.content
                for event in self._event_stream.get_events(reverse=True)
                if isinstance(event, MessageAction)
                and event.source == EventSource.AGENT
            ),
            None,
        )

        return last_agent_message if last_agent_message is not None else ''

    def get_last_events(self, n: int) -> list[Event]:
        """Return the last n events from the event stream."""
        # dummy agent is using this
        # it should work, but it's not great to store temporary lists now just for a test
        end_id = self._event_stream.get_latest_event_id()
        start_id = max(0, end_id - n + 1)

        return list(
            event
            for event in self._event_stream.get_events(
                start_id=start_id,
                end_id=end_id,
                filter_out_type=self.filter_out,
            )
        )

    def has_delegation(self) -> bool:
        for event in self._event_stream.get_events():
            if isinstance(event, AgentDelegateObservation):
                return True
        return False
