from agenthub.codeact_agent import CodeActAgent
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
from opendevin.runtime.plugins import PluginRequirement

from .action_parser import SelfDiscoverResponseParser
from .prompt import (
    SYSTEM_MESSAGE,
    get_prompt,
)
from .state_machine import SelfDiscoverStateMachine


class SelfDiscoverAgent(Agent):
    VERSION = '0.1'
    """
    This agent implements a Self Discover Agent after https://arxiv.org/abs/2402.03620.

    It generates a plan, which is then sent to the CodeActAgent to execute.
    To derive the plan so it has the option to use the BrowsingAgent and may also ask questions to the user.

    """

    action_parser = SelfDiscoverResponseParser()
    sandbox_plugins: list[PluginRequirement] = CodeActAgent.sandbox_plugins

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the SelfDiscoveryAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        self.self_discover_state_machine: SelfDiscoverStateMachine = (
            SelfDiscoverStateMachine()
        )
        super().__init__(llm)
        self.reset()

    def reset(self) -> None:
        """
        Resets the Agent.
        """
        # self.has_advanced = True
        self.self_discover_state_machine.reset()
        super().reset()

    def action_to_str(self, action: Action) -> str:
        if isinstance(action, AgentDelegateAction):
            if action.agent == 'CodeActAgent':
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
            self.self_discover_state_machine.reset()
            return AgentFinishAction()

        # add self discover prompt to messages
        # if self.has_advanced:
        task = state.get_current_user_intent()
        sdstate = self.self_discover_state_machine.current_state
        if prompt := get_prompt(task, sdstate):
            messages.append(prompt)

        # print(f"self.has_advanced: {self.has_advanced}\n")

        # print(f'messages:\n{messages}\n')

        # print(
        #     f'current step:\n{self.self_discover_state_machine.current_state}. \n\n previous step:\n{self.self_discover_state_machine.prev_state}'
        # )

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
        self.self_discover_state_machine.transition(action)
        return action
