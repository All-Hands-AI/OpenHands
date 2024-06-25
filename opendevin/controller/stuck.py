from typing import cast

from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action.action import Action
from opendevin.events.action.commands import CmdKillAction
from opendevin.events.action.empty import NullAction
from opendevin.events.action.message import MessageAction
from opendevin.events.event import Event, EventSource
from opendevin.events.observation.commands import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.error import ErrorObservation
from opendevin.events.observation.observation import Observation


class StuckDetector:
    def __init__(self, state: State):
        self.state = state

    def is_stuck(self):
        # filter out MessageAction with source='user' from history
        filtered_history = [
            event
            for event in self.state.history.get_events()
            if not (
                (isinstance(event, MessageAction) and event.source == EventSource.USER)
                or
                # there might be some NullAction or NullObservation in the history at least for now
                isinstance(event, NullAction)
                or isinstance(event, NullObservation)
            )
        ]

        # scenario 1: same action, same observation
        # it takes 3 actions and 3 observations to detect a loop
        if len(filtered_history) < 3:
            return False

        last_actions: list[Event] = []
        last_observations: list[Event] = []
        # retrieve the last three actions and observations starting from the end of history, wherever they are
        for event in reversed(filtered_history):
            if isinstance(event, Action) and len(last_actions) < 4:
                last_actions.append(event)
            elif isinstance(event, Observation) and len(last_observations) < 4:
                last_observations.append(event)

            if len(last_actions) == 4 and len(last_observations) == 4:
                break

        # are the last three actions the same?
        last_three_actions = last_actions[-3:]
        last_three_observations = last_observations[-3:]
        if len(last_three_actions) == 3 and all(
            self._eq_no_pid(last_three_actions[0], action)
            for action in last_three_actions
        ):
            if len(last_three_observations) == 3 and all(
                self._eq_no_pid(last_three_observations[0], observation)
                for observation in last_three_observations
            ):
                logger.warning('Action, Observation loop detected')
                return True

        # scenario 2: same action, errors
        # it takes 4 actions and 4 observations to detect a loop
        # check if the last four actions are the same and result in errors
        # retrieve the last four actions and observations starting from the end of history, wherever they are

        # are the last four actions the same?
        if len(last_actions) == 4 and all(
            self._eq_no_pid(last_actions[0], action) for action in last_actions
        ):
            # and the last four observations all errors?
            if all(isinstance(obs, ErrorObservation) for obs in last_observations):
                logger.warning('Action, ErrorObservation loop detected')
                return True
            # or, are the last four observations all IPythonRunCellObservation with SyntaxError?
            elif all(
                isinstance(obs, IPythonRunCellObservation) for obs in last_observations
            ) and all(
                cast(IPythonRunCellObservation, obs)
                .content[-100:]
                .find('SyntaxError: unterminated string literal (detected at line')
                != -1
                and len(
                    cast(IPythonRunCellObservation, obs).content.split(
                        'SyntaxError: unterminated string literal (detected at line'
                    )[-1]
                )
                < 10
                for obs in last_observations
            ):
                logger.warning('Action, IPythonRunCellObservation loop detected')
                return True

        # scenario 3: monologue
        # check for repeated MessageActions with source=AGENT
        # see if the agent is engaged in a good old monologue, telling itself the same thing over and over
        agent_message_actions = [
            (i, event)
            for i, event in enumerate(filtered_history)
            if isinstance(event, MessageAction) and event.source == EventSource.AGENT
        ]

        # last three message actions will do for this check
        if len(agent_message_actions) >= 3:
            last_agent_message_actions = agent_message_actions[-3:]

            if all(
                self._eq_no_pid(last_agent_message_actions[0][1], action[1])
                for action in last_agent_message_actions
            ):
                # check if there are any observations between the repeated MessageActions
                # then it's not yet a loop, maybe it can recover
                start_index = last_agent_message_actions[0][0]
                end_index = last_agent_message_actions[-1][0]

                has_observation_between = False
                for event in filtered_history[start_index + 1 : end_index]:
                    if isinstance(event, Observation):
                        has_observation_between = True
                        break

                if not has_observation_between:
                    logger.warning('Repeated MessageAction with source=AGENT detected')
                    return True

        # scenario 4: action, observation pattern on the last six steps
        # check if the agent repeats the same (Action, Observation)
        # every other step in the last six steps
        last_six_actions: list[Event] = []
        last_six_observations: list[Event] = []

        # the end of history is most interesting
        for event in reversed(filtered_history):
            if isinstance(event, Action) and len(last_six_actions) < 6:
                last_six_actions.append(event)
            elif isinstance(event, Observation) and len(last_six_observations) < 6:
                last_six_observations.append(event)

            if len(last_six_actions) == 6 and len(last_six_observations) == 6:
                break

        # this pattern is every other step, like:
        # (action_1, obs_1), (action_2, obs_2), (action_1, obs_1), (action_2, obs_2),...
        if len(last_six_actions) == 6 and len(last_six_observations) == 6:
            actions_equal = (
                # action_0 == action_2 == action_4
                self._eq_no_pid(last_six_actions[0], last_six_actions[2])
                and self._eq_no_pid(last_six_actions[0], last_six_actions[4])
                # action_1 == action_3 == action_5
                and self._eq_no_pid(last_six_actions[1], last_six_actions[3])
                and self._eq_no_pid(last_six_actions[1], last_six_actions[5])
            )
            observations_equal = (
                # obs_0 == obs_2 == obs_4
                self._eq_no_pid(last_six_observations[0], last_six_observations[2])
                and self._eq_no_pid(last_six_observations[0], last_six_observations[4])
                # obs_1 == obs_3 == obs_5
                and self._eq_no_pid(last_six_observations[1], last_six_observations[3])
                and self._eq_no_pid(last_six_observations[1], last_six_observations[5])
            )

            if actions_equal and observations_equal:
                logger.warning('Action, Observation pattern detected')
                return True

        return False

    def _eq_no_pid(self, obj1, obj2):
        if isinstance(obj1, CmdOutputObservation) and isinstance(
            obj2, CmdOutputObservation
        ):
            # for loop detection, ignore command_id, which is the pid
            return obj1.command == obj2.command and obj1.exit_code == obj2.exit_code
        elif isinstance(obj1, CmdKillAction) and isinstance(obj2, CmdKillAction):
            # for loop detection, ignore command_id, which is the pid
            return obj1.thought == obj2.thought
        else:
            # this is the default comparison
            return obj1 == obj2
