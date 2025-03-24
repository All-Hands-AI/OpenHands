import json
import os

import openhands.agenthub.proxy_agent.function_calling as proxy_function_calling
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
    RecallAction,
)
from openhands.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    ErrorObservation,
    IPythonRunCellObservation,
    RecallObservation,
    UserRejectObservation,
)
from openhands.events.observation.observation import Observation
from openhands.events.serialization.event import truncate_content
from openhands.llm.llm import LLM
from openhands.memory.condenser import Condenser
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from openhands.utils.prompt import PromptManager


class ProxyAgent(Agent):
    sandbox_plugins: list[PluginRequirement] = [
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]

    def __init__(self, llm: LLM, config: AgentConfig) -> None:
        super().__init__(llm, config)
        self.reset()

        self.mock_function_calling = False
        if not self.llm.is_function_calling_active():
            logger.info(
                f'Function calling not enabled for model {self.llm.config.model}. '
                'Mocking function calling via prompting.'
            )
            self.mock_function_calling = True

        # Function calling mode
        self.tools = proxy_function_calling.get_tools()

        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )

        self.condenser = Condenser.from_config(self.config.condenser)
        logger.debug(f'Using condenser: {self.condenser}')

        agent_list_path = os.path.join(os.path.dirname(__file__), 'agent_list.json')
        if not os.path.exists(agent_list_path):
            raise FileNotFoundError('agent list file not found')
        with open(agent_list_path, 'r') as f:
            self.agent_list = json.load(f)
            if self.agent_list == {}:
                raise ValueError('agent list file is empty')

    def step(self, state: State) -> Action:
        # Prepare the message to send to the LLM
        messages = self._get_messages(state)
        params: dict = {
            'messages': self.llm.format_messages_for_llm(messages),
        }
        params['tools'] = self.tools
        if self.mock_function_calling:
            params['mock_function_calling'] = True
        response = self.llm.completion(**params)

        # Assume only one tool call is returned
        action = proxy_function_calling.response_to_action(response)
        return action

    def _get_messages(self, state: State) -> list[Message]:
        if not self.prompt_manager:
            raise Exception('Prompt Manager not instantiated.')

        messages: list[Message] = [
            Message(
                role='system',
                content=[TextContent(text=self.prompt_manager.get_system_message())],
            ),
            Message(
                role='system',
                content=[
                    TextContent(
                        text='Available agents are the following:'
                        + json.dumps(self.agent_list)
                    )
                ],
            ),
        ]

        for event in state.history:
            if isinstance(event, Action):
                messages.append(self._get_action_message(event))
            elif isinstance(event, Observation):
                messages.append(self._get_observation_message(event))
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

        return messages

    def _get_observation_message(self, observation: Observation) -> Message:
        message: Message
        max_message_chars = self.llm.config.max_message_chars
        if isinstance(observation, IPythonRunCellObservation):
            message = Message(
                role='system',
                content=[TextContent(text=f'IPython Output\n{observation.content}')],
            )
        elif isinstance(observation, AgentDelegateObservation):
            text = observation.content + '\nOutputs: ' + json.dumps(observation.outputs)
            message = Message(role='system', content=[TextContent(text=text)])
        elif isinstance(observation, ErrorObservation):
            text = truncate_content(observation.content, max_message_chars)
            text += '\n[Error occurred in processing last action]'
            message = Message(role='system', content=[TextContent(text=text)])
        elif isinstance(observation, UserRejectObservation):
            text = 'OBSERVATION:\n' + truncate_content(
                observation.content, max_message_chars
            )
            text += '\n[Last action has been rejected by the user]'
            message = Message(role='system', content=[TextContent(text=text)])
        elif isinstance(observation, CmdOutputObservation):
            # Proxy Agent doesn't issue CmdRunAction. If there is a CmdOutputObservation, it's triggered by a user.
            text = truncate_content(
                f'\nObserved result of command executed by user:\n{observation.to_agent_observation()}',
                max_message_chars,
            )
            message = Message(role='system', content=[TextContent(text=text)])
        elif isinstance(observation, RecallObservation):
            message = Message(
                role='system',
                content=[TextContent(text=str(observation))],
            )
        else:
            raise ValueError(f'Unknown observation type: {type(observation)}')

        return message

    def _get_action_message(self, action: Action) -> Message:
        message: Message
        if isinstance(action, IPythonRunCellAction):
            message = Message(role='system', content=[TextContent(text=str(action))])
        elif isinstance(action, AgentDelegateAction):
            text = action.message + '\ninputs: ' + json.dumps(action.inputs)
            if action.thought:
                text += '\nthought: ' + action.thought
            message = Message(role='system', content=[TextContent(text=text)])
        elif isinstance(action, AgentFinishAction):
            text = action.message
            if action.outputs:
                text += '\noutputs: ' + json.dumps(action.outputs)
            message = Message(role='system', content=[TextContent(text=text)])
        elif isinstance(action, MessageAction):
            role = 'user' if action.source == 'user' else 'assistant'
            content = [TextContent(text=action.content or '')]
            message = Message(
                role=role,
                content=content,
            )
        elif isinstance(action, CmdRunAction):
            # Proxy Agent doesn't issue CmdRunAction. If there is, it's triggered by a user.
            message = Message(
                role='user',
                content=[
                    TextContent(text=f'User executed the command:\n{action.command}')
                ],
            )
        elif isinstance(action, RecallAction):
            text = str(action)
            if action.thought:
                text += '\nthought: ' + action.thought
            message = Message(role='system', content=[TextContent(text=text)])
        else:
            raise ValueError(f'Unknown action type: {type(action)}')

        return message

    def reset(self) -> None:
        super().reset()
