from openhands.core.logger import openhands_logger as logger
from openhands.events.action.action import Action
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource


class ReplayManager:
    """ReplayManager manages the lifecycle of a replay session of a given trajectory.

    Replay manager keeps track of a list of events, replays actions, and ignore
    messages and observations. It could lead to unexpected or even errorneous
    results if any action is non-deterministic, or if the initial state before
    the replay session is different from the initial state of the trajectory.
    """

    def __init__(self, replay_events: list[Event] | None):
        if replay_events:
            logger.info(f'Replay events loaded, events length = {len(replay_events)}')
            for index in range(len(replay_events) - 1):
                event = replay_events[index]
                if isinstance(event, MessageAction) and event.wait_for_response:
                    # For any message waiting for response that is not the last
                    # event, we override wait_for_response to True, as a response
                    # would have been included in the next event, and we don't
                    # want the user to interfere with the replay process
                    logger.info(
                        'Replay events contains wait_for_response message action, ignoring wait_for_response'
                    )
                    event.wait_for_response = False

        self.replay_events = replay_events
        self.replay_mode = bool(replay_events)
        self.replay_index = 0

    def _replayable(self) -> bool:
        return (
            self.replay_events is not None
            and self.replay_index < len(self.replay_events)
            and isinstance(self.replay_events[self.replay_index], Action)
            and self.replay_events[self.replay_index].source != EventSource.USER
        )

    def should_replay(self) -> bool:
        """
        Whether the controller is in trajectory replay mode, and the replay
        hasn't finished. Note: after the replay is finished, the user and
        the agent could continue to message/act.

        This method also moves "replay_index" to the next action, if applicable.
        """
        if not self.replay_mode:
            return False

        assert self.replay_events is not None
        while self.replay_index < len(self.replay_events) and not self._replayable():
            self.replay_index += 1

        return self._replayable()

    def step(self) -> Action:
        assert self.replay_events is not None
        event = self.replay_events[self.replay_index]
        assert isinstance(event, Action)
        self.replay_index += 1
        return event
