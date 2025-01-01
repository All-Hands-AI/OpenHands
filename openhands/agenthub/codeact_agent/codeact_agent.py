import os
from collections import deque

from litellm import ModelResponse

import openhands.agenthub.codeact_agent.function_calling as codeact_function_calling
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import ImageContent, Message, TextContent
from openhands.core.utils import json
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.observation import (
    AgentDelegateObservation,
    BrowserOutputObservation,
    CmdOutputObservation,
    FileEditObservation,
    FileReadObservation,
    IPythonRunCellObservation,
    UserRejectObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.observation import Observation
from openhands.events.serialization.event import truncate_content
from openhands.llm.llm import LLM
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
    ) -> None:
        """Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """

        # import pdb; pdb.set_trace()
        llm_config = LLMConfig(
            model='litellm_proxy/claude-3-5-sonnet-20241022',
            api_key='REDACTED',
            temperature=0.0,
            base_url='https://llm-proxy.app.all-hands.dev',
        )
        llm = LLM(llm_config)
        # TODO: Remove this once we have a real AgentConfig
        config = AgentConfig()
        super().__init__(llm, config)
        self.pending_actions: deque[Action] = deque()
        self.reset()

        self.mock_function_calling = False
        if not self.llm.is_function_calling_active():
            logger.info(
                f'Function calling not enabled for model {self.llm.config.model}. '
                'Mocking function calling via prompting.'
            )
            self.mock_function_calling = True

        # Function calling mode
        self.tools = codeact_function_calling.get_tools(
            codeact_enable_browsing=self.config.codeact_enable_browsing,
            codeact_enable_jupyter=self.config.codeact_enable_jupyter,
            codeact_enable_llm_editor=self.config.codeact_enable_llm_editor,
        )
        logger.debug(
            f'TOOLS loaded for CodeActAgent: {json.dumps(self.tools, indent=2, ensure_ascii=False).replace("\\n", "\n")}'
        )
        self.prompt_manager = PromptManager(
            microagent_dir=os.path.join(os.path.dirname(__file__), 'micro')
            if self.config.use_microagents
            else None,
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
            disabled_microagents=self.config.disabled_microagents,
        )

    def get_action_message(
        self,
        action: Action,
        pending_tool_call_action_messages: dict[str, Message],
    ) -> list[Message]:
        """Converts an action into a message format that can be sent to the LLM.

        This method handles different types of actions and formats them appropriately:
        1. For tool-based actions (AgentDelegate, CmdRun, IPythonRunCell, FileEdit) and agent-sourced AgentFinish:
            - In function calling mode: Stores the LLM's response in pending_tool_call_action_messages
            - In non-function calling mode: Creates a message with the action string
        2. For MessageActions: Creates a message with the text content and optional image content

        Args:
            action (Action): The action to convert. Can be one of:
                - CmdRunAction: For executing bash commands
                - IPythonRunCellAction: For running IPython code
                - FileEditAction: For editing files
                - FileReadAction: For reading files using openhands-aci commands
                - BrowseInteractiveAction: For browsing the web
                - AgentFinishAction: For ending the interaction
                - MessageAction: For sending messages
            pending_tool_call_action_messages (dict[str, Message]): Dictionary mapping response IDs
                to their corresponding messages. Used in function calling mode to track tool calls
                that are waiting for their results.

        Returns:
            list[Message]: A list containing the formatted message(s) for the action.
                May be empty if the action is handled as a tool call in function calling mode.

        Note:
            In function calling mode, tool-based actions are stored in pending_tool_call_action_messages
            rather than being returned immediately. They will be processed later when all corresponding
            tool call results are available.
        """
        # create a regular message from an event
        if isinstance(
            action,
            (
                AgentDelegateAction,
                IPythonRunCellAction,
                FileEditAction,
                FileReadAction,
                BrowseInteractiveAction,
                BrowseURLAction,
            ),
        ) or (isinstance(action, CmdRunAction) and action.source == 'agent'):
            tool_metadata = action.tool_call_metadata
            assert tool_metadata is not None, (
                'Tool call metadata should NOT be None when function calling is enabled. Action: '
                + str(action)
            )

            llm_response: ModelResponse = tool_metadata.model_response
            assistant_msg = llm_response.choices[0].message

            # Add the LLM message (assistant) that initiated the tool calls
            # (overwrites any previous message with the same response_id)
            logger.debug(
                f'Tool calls type: {type(assistant_msg.tool_calls)}, value: {assistant_msg.tool_calls}'
            )
            pending_tool_call_action_messages[llm_response.id] = Message(
                role=assistant_msg.role,
                # tool call content SHOULD BE a string
                content=[TextContent(text=assistant_msg.content or '')]
                if assistant_msg.content is not None
                else [],
                tool_calls=assistant_msg.tool_calls,
            )
            return []
        elif isinstance(action, AgentFinishAction):
            role = 'user' if action.source == 'user' else 'assistant'

            # when agent finishes, it has tool_metadata
            # which has already been executed, and it doesn't have a response
            # when the user finishes (/exit), we don't have tool_metadata
            tool_metadata = action.tool_call_metadata
            if tool_metadata is not None:
                # take the response message from the tool call
                assistant_msg = tool_metadata.model_response.choices[0].message
                content = assistant_msg.content or ''

                # save content if any, to thought
                if action.thought:
                    if action.thought != content:
                        action.thought += '\n' + content
                else:
                    action.thought = content

                # remove the tool call metadata
                action.tool_call_metadata = None
            return [
                Message(
                    role=role,
                    content=[TextContent(text=action.thought)],
                )
            ]
        elif isinstance(action, MessageAction):
            role = 'user' if action.source == 'user' else 'assistant'
            content = [TextContent(text=action.content or '')]
            if self.llm.vision_is_active() and action.image_urls:
                content.append(ImageContent(image_urls=action.image_urls))
            return [
                Message(
                    role=role,
                    content=content,
                )
            ]
        elif isinstance(action, CmdRunAction) and action.source == 'user':
            content = [
                TextContent(text=f'User executed the command:\n{action.command}')
            ]
            return [
                Message(
                    role='user',
                    content=content,
                )
            ]
        return []

    def get_observation_message(
        self,
        obs: Observation,
        tool_call_id_to_message: dict[str, Message],
    ) -> list[Message]:
        """Converts an observation into a message format that can be sent to the LLM.

        This method handles different types of observations and formats them appropriately:
        - CmdOutputObservation: Formats command execution results with exit codes
        - IPythonRunCellObservation: Formats IPython cell execution results, replacing base64 images
        - FileEditObservation: Formats file editing results
        - FileReadObservation: Formats file reading results from openhands-aci
        - AgentDelegateObservation: Formats results from delegated agent tasks
        - ErrorObservation: Formats error messages from failed actions
        - UserRejectObservation: Formats user rejection messages

        In function calling mode, observations with tool_call_metadata are stored in
        tool_call_id_to_message for later processing instead of being returned immediately.

        Args:
            obs (Observation): The observation to convert
            tool_call_id_to_message (dict[str, Message]): Dictionary mapping tool call IDs
                to their corresponding messages (used in function calling mode)

        Returns:
            list[Message]: A list containing the formatted message(s) for the observation.
                May be empty if the observation is handled as a tool response in function calling mode.

        Raises:
            ValueError: If the observation type is unknown
        """
        message: Message
        max_message_chars = self.llm.config.max_message_chars
        if isinstance(obs, CmdOutputObservation):
            # if it doesn't have tool call metadata, it was triggered by a user action
            if obs.tool_call_metadata is None:
                text = truncate_content(
                    f'\nObserved result of command executed by user:\n{obs.content}',
                    max_message_chars,
                )
            else:
                text = truncate_content(
                    obs.content + obs.interpreter_details, max_message_chars
                )
            text += f'\n[Command finished with exit code {obs.exit_code}]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, IPythonRunCellObservation):
            text = obs.content
            # replace base64 images with a placeholder
            splitted = text.split('\n')
            for i, line in enumerate(splitted):
                if '![image](data:image/png;base64,' in line:
                    splitted[i] = (
                        '![image](data:image/png;base64, ...) already displayed to user'
                    )
            text = '\n'.join(splitted)
            text = truncate_content(text, max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, FileEditObservation):
            text = truncate_content(str(obs), max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, FileReadObservation):
            message = Message(
                role='user', content=[TextContent(text=obs.content)]
            )  # Content is already truncated by openhands-aci
        elif isinstance(obs, BrowserOutputObservation):
            text = obs.get_agent_obs_text()
            message = Message(
                role='user',
                content=[TextContent(text=text)],
            )
        elif isinstance(obs, AgentDelegateObservation):
            text = truncate_content(
                obs.outputs['content'] if 'content' in obs.outputs else '',
                max_message_chars,
            )
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, ErrorObservation):
            text = truncate_content(obs.content, max_message_chars)
            text += '\n[Error occurred in processing last action]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, UserRejectObservation):
            text = 'OBSERVATION:\n' + truncate_content(obs.content, max_message_chars)
            text += '\n[Last action has been rejected by the user]'
            message = Message(role='user', content=[TextContent(text=text)])
        else:
            # If an observation message is not returned, it will cause an error
            # when the LLM tries to return the next message
            raise ValueError(f'Unknown observation type: {type(obs)}')

        # Update the message as tool response properly
        if (tool_call_metadata := obs.tool_call_metadata) is not None:
            tool_call_id_to_message[tool_call_metadata.tool_call_id] = Message(
                role='tool',
                content=message.content,
                tool_call_id=tool_call_metadata.tool_call_id,
                name=tool_call_metadata.function_name,
            )
            # No need to return the observation message
            # because it will be added by get_action_message when all the corresponding
            # tool calls in the SAME request are processed
            return []

        return [message]

    def reset(self) -> None:
        """Resets the CodeAct Agent."""
        super().reset()
        self.pending_actions.clear()

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

        # If this agent has a supervisor, we need to get the time to stop from the supervisor
        if self.when_to_stop < 0 and state.inputs.get('when_to_stop', None):
            self.when_to_stop: bool = state.inputs['when_to_stop']

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
        if self.mock_function_calling:
            params['mock_function_calling'] = True
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

        messages: list[Message] = [
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
        example_message = self.prompt_manager.get_example_user_message()
        if example_message:
            messages.append(
                Message(
                    role='user',
                    content=[TextContent(text=example_message)],
                    cache_prompt=self.llm.is_caching_prompt_active(),
                )
            )

        pending_tool_call_action_messages: dict[str, Message] = {}
        tool_call_id_to_message: dict[str, Message] = {}
        events = list(state.history)
        if self.number_of_events < 0:
            self.number_of_events: int = len(events)
        for i, event in enumerate(events):
            # create a regular message from an event
            if isinstance(event, Action):
                messages_to_add = self.get_action_message(
                    action=event,
                    pending_tool_call_action_messages=pending_tool_call_action_messages,
                )
            elif isinstance(event, Observation):
                messages_to_add = self.get_observation_message(
                    obs=event,
                    tool_call_id_to_message=tool_call_id_to_message,
                )
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            if i == self.number_of_events and state.inputs.get('next_step', ''):
                messages_to_add = [
                    Message(
                        role='user',
                        content=[TextContent(text=state.inputs['next_step'])],
                    )
                ]

            # Check pending tool call action messages and see if they are complete
            _response_ids_to_remove = []
            for (
                response_id,
                pending_message,
            ) in pending_tool_call_action_messages.items():
                assert pending_message.tool_calls is not None, (
                    'Tool calls should NOT be None when function calling is enabled & the message is considered pending tool call. '
                    f'Pending message: {pending_message}'
                )
                if all(
                    tool_call.id in tool_call_id_to_message
                    for tool_call in pending_message.tool_calls
                ):
                    # If complete:
                    # -- 1. Add the message that **initiated** the tool calls
                    messages_to_add.append(pending_message)
                    # -- 2. Add the tool calls **results***
                    for tool_call in pending_message.tool_calls:
                        messages_to_add.append(tool_call_id_to_message[tool_call.id])
                        tool_call_id_to_message.pop(tool_call.id)
                    _response_ids_to_remove.append(response_id)
            # Cleanup the processed pending tool messages
            for response_id in _response_ids_to_remove:
                pending_tool_call_action_messages.pop(response_id)

            for message in messages_to_add:
                if message:
                    if message.role == 'user':
                        self.prompt_manager.enhance_message(message)
                    messages.append(message)

        if self.number_of_events == len(events) and state.inputs.get('next_step', ''):
            messages.append(
                Message(
                    role='user', content=[TextContent(text=state.inputs['next_step'])]
                )
            )

        if self.llm.is_caching_prompt_active():
            # NOTE: this is only needed for anthropic
            # following logic here:
            # https://github.com/anthropics/anthropic-quickstarts/blob/8f734fd08c425c6ec91ddd613af04ff87d70c5a0/computer-use-demo/computer_use_demo/loop.py#L241-L262
            breakpoints_remaining = 3  # remaining 1 for system/tool
            for message in reversed(messages):
                if message.role == 'user' or message.role == 'tool':
                    if breakpoints_remaining > 0:
                        message.content[
                            -1
                        ].cache_prompt = True  # Last item inside the message content
                        breakpoints_remaining -= 1
                    else:
                        break

        return messages
