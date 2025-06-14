import json
import os

import openhands.agenthub.proxy_agent.function_calling as proxy_function_calling
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import Action, MessageAction
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.memory.conversation_memory import ConversationMemory
from openhands.microagent.prompt_manager import PromptManager
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)


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

        self._prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )

        # Create a ConversationMemory instance
        # _prompt_manager is guaranteed to be set at this point
        assert self._prompt_manager is not None
        self.conversation_memory = ConversationMemory(self.config, self._prompt_manager)

        agent_list_path = os.path.join(os.path.dirname(__file__), 'agent_list.json')
        if not os.path.exists(agent_list_path):
            raise FileNotFoundError('agent list file not found')
        with open(agent_list_path, 'r') as f:
            self.agent_list = json.load(f)
            if self.agent_list == {}:
                raise ValueError('agent list file is empty')

    def step(self, state: State) -> Action:
        # Prepare the message to send to the LLM
        initial_user_message = self._get_initial_user_message(state.history)
        messages = self._get_messages(state.history, initial_user_message)

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

    def _get_initial_user_message(self, history: list[Event]) -> MessageAction:
        """Finds the initial user message action from the full history."""
        initial_user_message: MessageAction | None = None
        for event in history:
            if isinstance(event, MessageAction) and event.source == 'user':
                initial_user_message = event
                break

        if initial_user_message is None:
            # This should not happen in a valid conversation
            raise ValueError(
                'Initial user message not found in history. Please report this issue.'
            )
        return initial_user_message

    def _get_messages(
        self, events: list[Event], initial_user_message: MessageAction
    ) -> list[Message]:
        if not self.prompt_manager:
            raise Exception('Prompt Manager not instantiated.')

        # Use ConversationMemory to process events (including SystemMessageAction)
        messages = self.conversation_memory.process_events(
            condensed_history=events,
            initial_user_action=initial_user_message,
            max_message_chars=self.llm.config.max_message_chars,
            vision_is_active=self.llm.vision_is_active(),
        )

        agent_list_message = Message(
            role='system',
            content=[
                TextContent(
                    text='Available agents are the following:'
                    + json.dumps(self.agent_list)
                )
            ],
        )
        if len(messages) > 1:
            messages.insert(1, agent_list_message)
        else:
            messages.append(agent_list_message)

        if self.llm.is_caching_prompt_active():
            self.conversation_memory.apply_prompt_caching(messages)

        return messages

    def reset(self) -> None:
        super().reset()
