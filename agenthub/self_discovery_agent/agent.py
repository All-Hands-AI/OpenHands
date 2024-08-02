from enum import Enum

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    MessageAction,
)
from opendevin.events.observation import AgentDelegateObservation
from opendevin.events.observation.observation import Observation
from opendevin.events.serialization.event import truncate_content
from opendevin.llm.llm import LLM

from .action_parser import SelfDiscoverResponseParser
from .prompt import SYSTEM_MESSAGE, get_prompt


class SelfDiscoveryStep(Enum):
    PRE_STEP = 0
    SELECT = 1
    ADAPT = 2
    IMPLEMENT = 3
    SOLVE = 4
    FINISHED = 5


class SelfDiscoveryAgent(Agent):
    VERSION = '0.1'
    """
    This agent implements a Self Discovery Agent after https://arxiv.org/abs/2402.03620.

    It generates a plan, which is then sent to the CodeActAgent to execute.
    To derive the plan so it has the option to use the BrowsingAgent and may also ask questions to the user.

    """

    action_parser = SelfDiscoverResponseParser()

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the SelfDiscoveryAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        self.current_step: SelfDiscoveryStep = SelfDiscoveryStep.SELECT
        self.prev_step: SelfDiscoveryStep = SelfDiscoveryStep.PRE_STEP

        super().__init__(llm)
        self.reset()

    def action_to_str(self, action: Action) -> str:
        if isinstance(action, AgentDelegateAction):
            if action.agent == 'BrowsingAgent':
                return f'{action.thought}\n<execute_browse>\n{action.inputs["task"]}\n</execute_browse>'
            elif action.agent == 'CodeActAgent':
                return f'{action.thought}\n<execute_plan>\n{action.inputs["task"]}\n</execute_plan>'
            else:
                raise ValueError(f'Unknown delegate: {action.agent}')
        elif isinstance(action, MessageAction):
            return action.content
        elif isinstance(action, AgentFinishAction) and action.source == 'agent':
            return action.thought
        return ''

    def get_action_message(self, action: Action) -> dict[str, str] | None:
        if (
            isinstance(action, MessageAction)
            or isinstance(action, AgentDelegateAction)
            or (isinstance(action, AgentFinishAction) and action.source == 'agent')
        ):
            return {
                'role': 'user' if action.source == 'user' else 'assistant',
                'content': self.action_to_str(action),
            }
        return None

    def get_observation_message(self, obs: Observation) -> dict[str, str] | None:
        max_message_chars = self.llm.config.max_message_chars
        if isinstance(obs, AgentDelegateObservation):
            content = 'OBSERVATION:\n' + truncate_content(
                str(obs.outputs), max_message_chars
            )
            return {'role': 'user', 'content': content}
        return None

    def advance_self_discovery_step(self, action: Action):
        # only move to next step if not browsing or user ask
        if not (
            (
                isinstance(action, AgentDelegateAction)
                and action.agent == 'BrowsingAgent'
            )
            or (isinstance(action, MessageAction) and action.wait_for_response)
        ):
            self.current_step = SelfDiscoveryStep(self.current_step.value + 1)

    def reset(self) -> None:
        """
        Resets the Agent.
        """
        self.current_step = SelfDiscoveryStep.SELECT
        self.prev_step = SelfDiscoveryStep.PRE_STEP
        super().reset()

    def step(self, state: State) -> Action:
        """
        Parameters:
        - state (State): used to get updated info and background commands

        Returns:

        """

        # abort if user desires
        latest_user_message = state.history.get_last_user_message()
        if latest_user_message and latest_user_message.strip() == '/exit':
            return AgentFinishAction()

        # prepare what we want to send to the LLM
        messages: list[dict[str, str]] = self.get_messages(state)

        # Finish when plan as been executed by CodeActAgent
        if isinstance(state.history.get_last_action(), AgentFinishAction):
            return AgentFinishAction()

        # add self discobvery prompt to messages
        if self_discovery_message := get_prompt(self.prev_step, self.current_step):
            messages.append(self_discovery_message)

        response = self.llm.completion(
            messages=messages,
            stop=[
                '</execute_ask>',
                '</execute_browse>',
                '</execute_plan>',
            ],
            temperature=0.0,
        )
        action = self.action_parser.parse(response)

        self.prev_step = self.current_step
        self.current_step = self.advance_self_discovery_step(action)
        return action

    def get_messages(self, state: State) -> list[dict[str, str]]:
        messages = [
            {'role': 'system', 'content': SYSTEM_MESSAGE},
        ]

        for event in state.history.get_events():
            # create a regular message from an event
            if isinstance(event, Action):
                message = self.get_action_message(event)
            elif isinstance(event, Observation):
                message = self.get_observation_message(event)
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            # add regular message
            if message:
                messages.append(message)

        return messages
