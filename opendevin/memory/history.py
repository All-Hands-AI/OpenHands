from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action
from opendevin.events.action.agent import AgentSummarizeAction
from opendevin.events.action.empty import NullAction
from opendevin.events.event import Event
from opendevin.events.observation.commands import CmdOutputObservation
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.observation import Observation
from opendevin.events.observation.summary import SummaryObservation


class ShortTermHistory(list[Event]):
    """
    A list of events that represents the short-term memory of the agent.
    """

    def append(self, item: tuple[Action, Observation] | Event):
        """
        Append an event to the history. Accepts an (action, observation) tuple for compatibility on the short term.

        Args:
            event: The event to append.
        """
        if not isinstance(item, tuple) and not isinstance(item, Event):
            raise TypeError(f'Event must be a tuple, got {type(item)}')

        if isinstance(item, tuple):
            action, observation = item
            self.append(action)

            self.append(observation)
        elif isinstance(item, Event):
            if isinstance(item, AgentSummarizeAction):
                # we're not making an obs
                self.replace_events_with_summary(item)
            else:
                super().append(item)
        else:
            raise TypeError(f'Event must be a tuple or Event, got {type(item)}')

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

        for event in self.get_events():
            if event.id is None or event.id == -1:
                logger.debug(f'Event {event} has no ID')

            if event.id is None:
                # this will never happen (tm)
                continue

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
                        'This would become (NullAction, NullObservation), drop it instead'
                    )
                    continue
                if not isinstance(observation, CmdOutputObservation):
                    logger.debug(f'Observation {observation} has no cause')
                tuples.append((NullAction(), observation))

        return tuples.copy()

    def get_events(self) -> list[Event]:
        """
        Return the history as a list of Event objects.
        """
        return list(self)

    def replace_events_with_summary(self, summary_action: AgentSummarizeAction):
        start_id = summary_action._chunk_start
        end_id = summary_action._chunk_end

        # valid start and end indices for the chunk
        if start_id == -1 or end_id == -1 or start_id > end_id or end_id > len(self):
            # weird, but just return
            return

        # create the SummaryObservation based on the AgentSummarizeAction
        # do we need to do this?
        summary_observation = SummaryObservation(content=summary_action.summary)

        # clean up the action if we're doing it this way, this is odd
        summary_action.summary = ''

        # replace the events in the specified range with the summary action and observation
        self[start_id:end_id] = [summary_action, summary_observation]
