from typing import ClassVar, Iterable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action
from opendevin.events.action.agent import (
    AgentDelegateAction,
    AgentSummarizeAction,
    ChangeAgentStateAction,
)
from opendevin.events.action.empty import NullAction
from opendevin.events.action.message import MessageAction
from opendevin.events.event import Event, EventSource
from opendevin.events.observation.agent import AgentStateChangedObservation
from opendevin.events.observation.commands import CmdOutputObservation
from opendevin.events.observation.delegate import AgentDelegateObservation
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.observation import Observation
from opendevin.events.serialization.event import event_to_dict
from opendevin.events.stream import EventStream


class ShortTermHistory(list[Event]):
    """
    A list of events that represents the short-term memory of the agent.
    """

    start_id: int
    end_id: int
    _event_stream: EventStream
    summaries: dict[tuple[int, int], AgentSummarizeAction]
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
        self.summaries = {}
        self.delegates = {}

    def set_event_stream(self, event_stream: EventStream):
        self._event_stream = event_stream

    def get_events_as_list(self) -> list[Event]:
        """
        Return the history as a list of Event objects.
        """
        return list(self.get_events())

    def get_events(self, reverse: bool = False) -> Iterable[Event]:
        """
        Return the events as a stream of Event objects.
        """
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
            if event.id in [chunk_start for chunk_start, _ in self.summaries.keys()]:
                chunk_start, chunk_end = next(
                    (chunk_start, chunk_end)
                    for chunk_start, chunk_end in self.summaries.keys()
                    if chunk_start == event.id
                )
                summary_action = self.summaries[(chunk_start, chunk_end)]
                yield summary_action
            elif not any(
                chunk_start <= event.id <= chunk_end
                for chunk_start, chunk_end in self.summaries.keys()
            ):
                yield event

    def get_last_action(self, end_id: int = -1) -> Action | None:
        """
        Return the last action from the event stream, filtered to exclude unwanted events.
        """
        end_id = self._event_stream.get_latest_event_id() if end_id == -1 else end_id

        last_action = next(
            (
                event
                for event in self._event_stream.get_events(end_id=end_id, reverse=True)
                if isinstance(event, Action)
                and not isinstance(event, (NullAction, ChangeAgentStateAction))
            ),
            None,
        )

        return last_action

    def get_last_observation(self, end_id: int = -1) -> Observation | None:
        """
        Return the last observation from the event stream, filtered to exclude unwanted events.
        """
        end_id = self._event_stream.get_latest_event_id() if end_id == -1 else end_id

        last_observation = next(
            (
                event
                for event in self._event_stream.get_events(end_id=end_id, reverse=True)
                if isinstance(event, Observation)
                and not isinstance(
                    event, (NullObservation, AgentStateChangedObservation)
                )
            ),
            None,
        )

        return last_observation

    def get_latest_user_message(self) -> str:
        """
        Return the latest user message from the event stream.
        """

        last_user_message = next(
            (
                event.content
                for event in self._event_stream.get_events(
                    reverse=True, filter_out_type=self.filter_out
                )
                if isinstance(event, MessageAction) and event.source == EventSource.USER
            ),
            None,
        )

        return last_user_message if last_user_message is not None else ''

    def get_last_events(self, n: int) -> list[Event]:
        """
        Return the last n events from the event stream.
        """
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

    def get_latest_event_id(self):
        return self._event_stream.get_latest_event_id()

    def add_summary(self, summary_action: AgentSummarizeAction):
        self.summaries[(summary_action._chunk_start, summary_action._chunk_end)] = (
            summary_action
        )

    def on_event(self, event: Event):
        if not isinstance(event, AgentDelegateObservation):
            return

        logger.info('AgentDelegateObservation received')
        # figure out what this delegate's actions were
        # from AgentDelegateAction to AgentDelegateObservation
        # and add their ids to exclude from parent stream
        # or summarize
        delegate_end = event.id
        delegate_start = -1
        delegate_agent: str = ''
        delegate_task: str = ''
        for prev_event in self._event_stream.get_events(
            end_id=event.id - 1, reverse=True
        ):
            if isinstance(prev_event, AgentDelegateAction):
                delegate_start = prev_event.id
                delegate_agent = prev_event.agent
                delegate_task = prev_event.inputs.get('task', '')
                break

        if delegate_start == -1:
            logger.error('No AgentDelegateAction found for AgentDelegateObservation')
            return

        self.delegates[(delegate_start, delegate_end)] = (delegate_agent, delegate_task)
        logger.info(
            f'Delegate {delegate_agent} with task {delegate_task} ran from id={delegate_start} to id={delegate_end}'
        )

    def compatibility_for_eval_history_tuples(self) -> list[tuple[dict, dict]]:
        history_tuples = []

        for action, observation in self.get_tuples():
            history_tuples.append((event_to_dict(action), event_to_dict(observation)))

        return history_tuples

    # TODO remove me when unnecessary
    # history is now available as a filtered stream of events, rather than list of pairs of (Action, Observation)
    # we rebuild the pairs here
    # for compatibility with the existing output format in evaluations
    def get_tuples(self) -> list[tuple[Action, Observation]]:
        """
        Return the history as a list of tuples (action, observation).
        """
        tuples: list[tuple[Action, Observation]] = []
        action_map: dict[int, Action] = {}
        observation_map: dict[int, Observation] = {}

        # runnable actions are set as cause of observations
        # (MessageAction, NullObservation) for source=USER
        # (MessageAction, NullObservation) for source=AGENT
        # (other_action?, NullObservation)
        # (NullAction, CmdOutputObservation)

        for event in self.get_events_as_list():
            if event.id is None or event.id == -1:
                logger.debug(f'Event {event} has no ID')

            if isinstance(event, Action):
                action_map[event.id] = event

            if isinstance(event, Observation):
                if event.cause is None or event.cause == -1:
                    logger.debug(f'Observation {event} has no cause')

                if event.cause is None:
                    # this will never happen (tm)
                    continue

                observation_map[event.cause] = event

        for action_id, action in action_map.items():
            observation = observation_map.get(action_id)
            if observation:
                # observation with a cause
                tuples.append((action, observation))
            else:
                tuples.append((action, NullObservation('')))

        for cause_id, observation in observation_map.items():
            if cause_id not in action_map:
                if isinstance(observation, NullObservation):
                    logger.debug(
                        "This would become (NullAction, NullObservation), which doesn't exist even today, drop it instead"
                    )
                    continue
                if not isinstance(observation, CmdOutputObservation):
                    logger.debug(f'Observation {observation} has no cause')
                tuples.append((NullAction(), observation))

        return tuples.copy()
