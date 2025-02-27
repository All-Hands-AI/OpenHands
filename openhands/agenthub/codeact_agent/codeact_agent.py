import json
import os
from collections import deque

import openhands
import openhands.agenthub.codeact_agent.function_calling as codeact_function_calling
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.message_utils import (
    apply_prompt_caching,
    events_to_messages,
)
from openhands.events.action import (
    Action,
    AgentFinishAction,
)
from openhands.events.stream import EventStream
from openhands.llm.llm import LLM
from openhands.memory.condenser import Condenser
from openhands.memory.conversation_memory import ConversationMemory
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from openhands.utils.prompt import PromptManager


class CodeActAgent(Agent):
    VERSION = '2.2'
    """
    The Code Act Agent is a minimalist agent.
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.

    ### Overview

    This agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a unified **code** action space for both *simplicity* and *performance* (see paper for more details).

    The conceptual idea is illustrated below. At each turn, the agent can:

    1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
    2. **CodeAct**: Choose to perform the task by executing code
    - Execute any valid Linux `bash` command
    - Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

    ![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

    """

    sandbox_plugins: list[PluginRequirement] = [
        # NOTE: AgentSkillsRequirement need to go before JupyterRequirement, since
        # AgentSkillsRequirement provides a lot of Python functions,
        # and it needs to be initialized before Jupyter for Jupyter to use those functions.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
        event_stream: EventStream = None,
    ) -> None:
        """Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        - event_stream (EventStream, optional): The event stream to use for conversation memory
        """
        super().__init__(llm, config)
        self.pending_actions: deque[Action] = deque()
        self.reset()

        # Retrieve the enabled tools
        self.tools = codeact_function_calling.get_tools(
            codeact_enable_browsing=self.config.codeact_enable_browsing,
            codeact_enable_jupyter=self.config.codeact_enable_jupyter,
            codeact_enable_llm_editor=self.config.codeact_enable_llm_editor,
        )
        logger.debug(
            f'TOOLS loaded for CodeActAgent: {json.dumps(self.tools, indent=2, ensure_ascii=False).replace("\\n", "\n")}'
        )
        
        # Initialize the prompt manager
        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )
        
        # Initialize conversation memory if event_stream is provided and prompt extensions are enabled
        self.conversation_memory = None
        if event_stream and self.config.enable_prompt_extensions:
            microagent_dir = os.path.join(
                os.path.dirname(os.path.dirname(openhands.__file__)),
                'microagents',
            )
            self.conversation_memory = ConversationMemory(
                event_stream=event_stream,
                microagents_dir=microagent_dir,
                disabled_microagents=self.config.disabled_microagents,
            )
            self.conversation_memory.set_prompt_manager(self.prompt_manager)

        self.condenser = Condenser.from_config(self.config.condenser)
        logger.debug(f'Using condenser: {self.condenser}')

    def reset(self) -> None:
        """Resets the CodeAct Agent."""
        super().reset()
        self.pending_actions.clear()
        
    def set_repository_info(self, repo_name: str, repo_directory: str) -> None:
        """Sets information about the GitHub repository that has been cloned.

        Args:
            repo_name: The name of the GitHub repository (e.g. 'owner/repo')
            repo_directory: The directory where the repository has been cloned
        """
        if self.conversation_memory:
            self.conversation_memory.set_repository_info(repo_name, repo_directory)
        else:
            self.prompt_manager.set_repository_info(
                RepositoryInfo(repo_name=repo_name, repo_directory=repo_directory)
            )
            
    def set_runtime_info(self, runtime_hosts: dict[str, int]) -> None:
        """Sets information about the runtime environment.

        Args:
            runtime_hosts: A dictionary mapping host names to port numbers
        """
        if self.conversation_memory:
            self.conversation_memory.set_runtime_info(runtime_hosts)
        else:
            from openhands.utils.prompt import RuntimeInfo
            self.prompt_manager.set_runtime_info(RuntimeInfo(available_hosts=runtime_hosts))

    def step(self, state: State) -> Action:
        """Performs one step using the CodeAct Agent.
        This includes gathering info on previous steps and prompting the model to make a command to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - CmdRunAction(command) - bash command to run
        - IPythonRunCellAction(code) - IPython code to run
        - AgentDelegateAction(agent, inputs) - delegate action for (sub)task
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        # Continue with pending actions if any
        if self.pending_actions:
            return self.pending_actions.popleft()

        # if we're done, go back
        latest_user_message = state.get_last_user_message()
        if latest_user_message and latest_user_message.content.strip() == '/exit':
            return AgentFinishAction()

        # prepare what we want to send to the LLM
        messages = self._get_messages(state)
        params: dict = {
            'messages': self.llm.format_messages_for_llm(messages),
        }
        params['tools'] = self.tools
        response = self.llm.completion(**params)
        actions = codeact_function_calling.response_to_actions(response)
        for action in actions:
            self.pending_actions.append(action)
        return self.pending_actions.popleft()

    def _get_messages(self, state: State) -> list[Message]:
        """Constructs the message history for the LLM conversation.

        This method builds a structured conversation history by processing events from the state
        and formatting them into messages that the LLM can understand. It handles both regular
        message flow and function-calling scenarios.

        The method performs the following steps:
        1. Initializes with system prompt and optional initial user message
        2. Processes events (Actions and Observations) into messages
        3. Handles tool calls and their responses in function-calling mode
        4. Manages message role alternation (user/assistant/tool)
        5. Applies caching for specific LLM providers (e.g., Anthropic)
        6. Adds environment reminders for non-function-calling mode

        Args:
            state (State): The current state object containing conversation history and other metadata

        Returns:
            list[Message]: A list of formatted messages ready for LLM consumption, including:
                - System message with prompt
                - Initial user message (if configured)
                - Action messages (from both user and assistant)
                - Observation messages (including tool responses)
                - Environment reminders (in non-function-calling mode)

        Note:
            - In function-calling mode, tool calls and their responses are carefully tracked
              to maintain proper conversation flow
            - Messages from the same role are combined to prevent consecutive same-role messages
            - For Anthropic models, specific messages are cached according to their documentation
        """
        if not self.prompt_manager:
            raise Exception('Prompt Manager not instantiated.')

        messages: list[Message] = self._initial_messages()

        # Condense the events from the state.
        events = self.condenser.condensed_history(state)

        messages += events_to_messages(
            events,
            max_message_chars=self.llm.config.max_message_chars,
            vision_is_active=self.llm.vision_is_active(),
            enable_som_visual_browsing=self.config.enable_som_visual_browsing,
        )

        messages = self._enhance_messages(messages)

        if self.llm.is_caching_prompt_active():
            apply_prompt_caching(messages)

        return messages

    def _initial_messages(self) -> list[Message]:
        """Creates the initial messages (including the system prompt) for the LLM conversation."""
        assert self.prompt_manager, 'Prompt Manager not instantiated.'

        return [
            Message(
                role='system',
                content=[
                    TextContent(
                        text=self.prompt_manager.get_system_message(),
                        cache_prompt=self.llm.is_caching_prompt_active(),
                    )
                ],
            )
        ]

    def _enhance_messages(self, messages: list[Message]) -> list[Message]:
        """Enhances the user message with additional context based on keywords matched.

        Args:
            messages (list[Message]): The list of messages to enhance

        Returns:
            list[Message]: The enhanced list of messages
        """
        assert self.prompt_manager, 'Prompt Manager not instantiated.'

        results: list[Message] = []
        is_first_message_handled = False

        for msg in messages:
            if msg.role == 'user' and not is_first_message_handled:
                is_first_message_handled = True
                # compose the first user message with examples
                self.prompt_manager.add_examples_to_initial_message(msg)

                # If we're not using conversation_memory, use the old approach
                if self.config.enable_prompt_extensions and not self.conversation_memory:
                    self.prompt_manager.add_info_to_initial_message(msg)

            # If we're not using conversation_memory, use the old approach for enhancing messages
            if msg.role == 'user' and not self.conversation_memory:
                self.prompt_manager.enhance_message(msg)

            results.append(msg)

        return results
