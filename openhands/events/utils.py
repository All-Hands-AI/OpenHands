from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import Action
from openhands.events.action.empty import NullAction
from openhands.events.event import Event
from openhands.events.observation import (
    CmdOutputObservation,
    NullObservation,
    Observation,
)


def get_pairs_from_events(events: list[Event]) -> list[tuple[Action, Observation]]:
    """Return the history as a list of tuples (action, observation).

    This function is a compatibility function for evals reading and visualization working with old histories."""
    tuples: list[tuple[Action, Observation]] = []
    action_map: dict[int, Action] = {}
    observation_map: dict[int, Observation] = {}

    # runnable actions are set as cause of observations
    # (MessageAction, NullObservation) for source=USER
    # (MessageAction, NullObservation) for source=AGENT
    # (other_action?, NullObservation)
    # (NullAction, CmdOutputObservation) background CmdOutputObservations

    for event in events:
        if event.id is None or event.id == -1:
            logger.debug(f'Event {event} has no ID')

        if isinstance(event, Action):
            action_map[event.id] = event

        if isinstance(event, Observation):
            if event.cause is None or event.cause == -1:
                logger.debug(f'Observation {event} has no cause')

            if event.cause is None:
                # runnable actions are set as cause of observations
                # NullObservations have no cause
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
                continue
            if not isinstance(observation, CmdOutputObservation):
                logger.debug(f'Observation {observation} has no cause')
            tuples.append((NullAction(), observation))

    return tuples.copy()
