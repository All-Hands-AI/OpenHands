import json
import os
from collections import defaultdict, deque
from itertools import islice

from litellm import ModelResponse

import openhands.agenthub.codeact_agent.function_calling as codeact_function_calling
from openhands.agenthub.codeact_agent.action_parser import CodeActResponseParser
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    FileEditAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    FileEditObservation,
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
from openhands.utils.microagent import MicroAgent
from openhands.utils.prompt import PromptManager


class CodeActAgent(Agent):
    VERSION = '2.1'
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
    obs_prefix = 'OBSERVATION:\n'

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm, config)
        self.reset()

        self.micro_agent = (
            MicroAgent(
                os.path.join(
                    os.path.dirname(__file__), 'micro', f'{config.micro_agent_name}.md'
                )
            )
            if config.micro_agent_name
            else None
        )
        if (
            self.config.function_calling
            and not self.llm.config.supports_function_calling
        ):
            logger.warning(
                f'Function calling not supported for model {self.llm.config.model}. '
                'Disabling function calling.'
            )
            self.config.function_calling = False

        if self.config.function_calling:
            # Function calling mode
            self.tools = codeact_function_calling.get_tools(
                codeact_enable_browsing_delegate=self.config.codeact_enable_browsing_delegate,
                codeact_enable_jupyter=self.config.codeact_enable_jupyter,
                codeact_enable_llm_editor=self.config.codeact_enable_llm_editor,
            )
            logger.info(
                f'TOOLS loaded for CodeActAgent: {json.dumps(self.tools, indent=2)}'
            )
            self.system_prompt = codeact_function_calling.SYSTEM_PROMPT
            self.initial_user_message = None
        else:
            # Non-function-calling mode
            self.action_parser = CodeActResponseParser()
            self.prompt_manager = PromptManager(
                prompt_dir=os.path.join(os.path.dirname(__file__)),
                agent_skills_docs=AgentSkillsRequirement.documentation,
                micro_agent=self.micro_agent,
            )
            self.system_prompt = self.prompt_manager.system_message
            self.initial_user_message = self.prompt_manager.initial_user_message

        self.pending_actions: deque[Action] = deque()

    def get_action_message(
        self,
        action: Action,
        response_id_tool_call_counter: dict[str, int],
        tool_call_id_to_message: dict[str, Message],
    ) -> list[Message]:
        """Convert an action to a message sent to the LLM."""
        # create a regular message from an event
        if isinstance(
            action,
            (
                AgentDelegateAction,
                CmdRunAction,
                IPythonRunCellAction,
                FileEditAction,
            ),
        ) or (isinstance(action, AgentFinishAction) and action.source == 'agent'):
            if self.config.function_calling:
                messages_to_add: list[Message] = []
                tool_metadata = action.tool_call_metadata
                assert tool_metadata is not None, (
                    'Tool call metadata should NOT be None when function calling is enabled. Action: '
                    + str(action)
                )

                # Check if all tool calls are processed
                if (
                    response_id_tool_call_counter[tool_metadata.model_response.id]
                    < tool_metadata.total_calls_in_response
                ):
                    response_id_tool_call_counter[tool_metadata.model_response.id] += 1
                    pass
                elif (
                    response_id_tool_call_counter[tool_metadata.model_response.id]
                    == tool_metadata.total_calls_in_response
                ):
                    # all tool calls are processed
                    llm_response: ModelResponse = tool_metadata.model_response
                    assistant_msg = llm_response.choices[0].message
                    # Add the LLM message (assistant) that initiated the tool calls
                    messages_to_add.append(
                        Message(
                            role=assistant_msg.role,
                            # tool call content SHOULD BE a string
                            content=[TextContent(text=assistant_msg.content)]
                            if assistant_msg.content is not None
                            else [],
                            tool_calls=assistant_msg.tool_calls,
                        )
                    )
                    # Add the tool calls **results***
                    for tool_call in assistant_msg.tool_calls:
                        messages_to_add.append(tool_call_id_to_message[tool_call.id])
                else:
                    raise ValueError('This should not happen')
                return messages_to_add
            else:
                content = [TextContent(text=self.action_parser.action_to_str(action))]
                return [
                    Message(
                        role='user' if action.source == 'user' else 'assistant',
                        content=content,
                    )
                ]
        elif isinstance(action, MessageAction):
            role = 'user' if action.source == 'user' else 'assistant'
            content = [TextContent(text=action.content)]
            if self.llm.vision_is_active() and action.images_urls:
                content.append(ImageContent(image_urls=action.images_urls))
            return [
                Message(
                    role=role,
                    content=content,
                )
            ]
        return []

    def get_observation_message(
        self,
        obs: Observation,
        tool_call_id_to_message: dict[str, Message],
    ) -> list[Message]:
        message: Message
        max_message_chars = self.llm.config.max_message_chars
        obs_prefix = 'OBSERVATION:\n'
        if isinstance(obs, CmdOutputObservation):
            text = obs_prefix + truncate_content(
                obs.content + obs.interpreter_details, max_message_chars
            )
            text += f'\n[Command finished with exit code {obs.exit_code}]'
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, IPythonRunCellObservation):
            text = obs_prefix + obs.content
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
            text = obs_prefix + truncate_content(str(obs), max_message_chars)
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, AgentDelegateObservation):
            text = obs_prefix + truncate_content(
                obs.outputs['content'] if 'content' in obs.outputs else '',
                max_message_chars,
            )
            message = Message(role='user', content=[TextContent(text=text)])
        elif isinstance(obs, ErrorObservation):
            text = obs_prefix + truncate_content(obs.content, max_message_chars)
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

        if self.config.function_calling:
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
        latest_user_message = state.history.get_last_user_message()
        if latest_user_message and latest_user_message.strip() == '/exit':
            return AgentFinishAction()

        # prepare what we want to send to the LLM
        messages = self._get_messages(state)
        params: dict = {
            'messages': self.llm.format_messages_for_llm(messages),
        }
        if self.config.function_calling:
            params['tools'] = self.tools
            params['parallel_tool_calls'] = False
        else:
            params['stop'] = [
                '</execute_ipython>',
                '</execute_bash>',
                '</execute_browse>',
                '</file_edit>',
            ]
        response = self.llm.completion(**params)

        # TODO: potentially handle MULTIPLE tool calls per response
        if self.config.function_calling:
            actions = codeact_function_calling.response_to_actions(response)
            for action in actions:
                self.pending_actions.append(action)
            return self.pending_actions.popleft()
        else:
            return self.action_parser.parse(response)

    def _get_messages(self, state: State) -> list[Message]:
        messages: list[Message] = [
            Message(
                role='system',
                content=[
                    TextContent(
                        text=self.system_prompt,
                        cache_prompt=self.llm.is_caching_prompt_active(),  # Cache system prompt
                    )
                ],
            )
        ]
        if self.initial_user_message:
            messages.append(
                Message(
                    role='user',
                    content=[TextContent(text=self.initial_user_message)],
                )
            )

        response_id_tool_call_counter: dict[str, int] = defaultdict(int)
        tool_call_id_to_message: dict[str, Message] = {}
        for event in state.history.get_events():
            # create a regular message from an event
            if isinstance(event, Action):
                messages_to_add = self.get_action_message(
                    action=event,
                    response_id_tool_call_counter=response_id_tool_call_counter,
                    tool_call_id_to_message=tool_call_id_to_message,
                )
            elif isinstance(event, Observation):
                messages_to_add = self.get_observation_message(
                    obs=event,
                    tool_call_id_to_message=tool_call_id_to_message,
                )
            else:
                raise ValueError(f'Unknown event type: {type(event)}')

            for message in messages_to_add:
                # add regular message
                if message:
                    # handle error if the message is the SAME role as the previous message
                    # litellm.exceptions.BadRequestError: litellm.BadRequestError: OpenAIException - Error code: 400 - {'detail': 'Only supports u/a/u/a/u...'}
                    # there shouldn't be two consecutive messages from the same role
                    if messages and messages[-1].role == message.role:
                        messages[-1].content.extend(message.content)
                    else:
                        messages.append(message)

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

        if not self.config.function_calling:
            # The latest user message is important:
            # we want to remind the agent of the environment constraints
            latest_user_message = next(
                islice(
                    (
                        m
                        for m in reversed(messages)
                        if m.role == 'user'
                        and any(isinstance(c, TextContent) for c in m.content)
                    ),
                    1,
                ),
                None,
            )
            # do not add this for function calling
            if latest_user_message:
                reminder_text = f'\n\nENVIRONMENT REMINDER: You have {state.max_iterations - state.iteration} turns left to complete the task. When finished reply with <finish></finish>.'
                latest_user_message.content.append(TextContent(text=reminder_text))

        return messages
