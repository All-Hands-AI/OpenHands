import json
import os
from collections import deque
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional, override

from httpx import request

import openhands.agenthub.codeact_agent.function_calling as codeact_function_calling
from openhands.a2a.A2AManager import A2AManager
from openhands.a2a.tool import ListRemoteAgents, SendTask
from openhands.agenthub.codeact_agent.tools.finish import FinishTool
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.core.schema import ResearchMode
from openhands.events.action import (
    Action,
    AgentFinishAction,
    StreamingMessageAction,
)
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.llm.llm import LLM, check_tools
from openhands.llm.streaming_llm import StreamingLLM
from openhands.memory.condenser import Condenser
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.conversation_memory import ConversationMemory
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from openhands.utils.async_utils import call_async_from_sync
from openhands.utils.prompt import PromptManager


class CodeActAgent(Agent):
    VERSION = '2.2'
    """
    The Code Act Agent is a minimalist agent.
    The agent works by passing the model a list of action-observation pairs and prompting the model to take the next step.

    ### Overview

    This agent implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents' **act**ions into a unified **code** action space for both *simplicity* and *performance* (see paper for more details).

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
        workspace_mount_path_in_sandbox_store_in_session: bool = True,
        a2a_manager: A2AManager | None = None,
        routing_llms: dict[str, LLM] | None = None,
        enable_streaming: bool = False,
        session_id: str | None = None,
    ) -> None:
        """Initializes a new instance of the CodeActAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        - workspace_mount_path_in_sandbox_store_in_session (bool, optional): Whether to store the workspace mount path in session. Defaults to True.
        - a2a_manager (A2AManager, optional): The A2A manager to be used by this agent. Defaults to None.
        """
        super().__init__(
            llm,
            config,
            workspace_mount_path_in_sandbox_store_in_session,
            a2a_manager,
        )
        self.pending_actions: deque[Action] = deque()
        self.reset()

        built_in_tools = codeact_function_calling.get_tools(
            codeact_enable_browsing=self.config.codeact_enable_browsing,
            codeact_enable_jupyter=self.config.codeact_enable_jupyter,
            codeact_enable_llm_editor=self.config.codeact_enable_llm_editor,
            llm=self.llm,
            enable_pyodide_bash=self.config.enable_pyodide,
        )

        self.tools = built_in_tools

        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )
        self.enable_streaming = enable_streaming
        self.session_id = session_id

        # Create a ConversationMemory instance
        self.conversation_memory = ConversationMemory(self.config, self.prompt_manager)
        if 'llm_config' in self.config.condenser:
            logger.info(f'Condenser config: {self.config.condenser.llm_config}')
        self.condenser = Condenser.from_config(self.config.condenser)
        logger.info(f'Using condenser: {type(self.condenser)}')
        self.routing_llms = routing_llms
        self.search_tools: list[dict] = []
        self.streaming_llm = (
            StreamingLLM(
                config=self.llm.config,
                session_id=self.session_id,
                user_id=self.llm.user_id,
            )
            if self.enable_streaming
            else None
        )
        self.streaming_routing_llm = (
            StreamingLLM(
                config=self.routing_llms['simple'].config,
                session_id=self.session_id,
                user_id=self.llm.user_id,
            )
            if self.enable_streaming
            and self.routing_llms
            and 'simple' in self.routing_llms
            else None
        )

    @override
    def set_system_prompt(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        if self.prompt_manager:
            self.prompt_manager.set_system_message(system_prompt)
        logger.info(
            f'New system prompt: {self.conversation_memory.process_initial_messages()}'
        )

    @override
    def set_user_prompt(self, user_prompt: str) -> None:
        self.user_prompt = user_prompt
        if self.prompt_manager:
            self.prompt_manager.set_user_message(user_prompt)
        logger.info(
            f'New user prompt: {self.conversation_memory.process_initial_messages()}'
        )

    def reset(self) -> None:
        """Resets the CodeAct Agent."""
        super().reset()
        self.pending_actions.clear()

    def _select_tools_based_on_mode(self, research_mode: str | None) -> list[dict]:
        """Selects the tools based on the mode of the agent."""
        if research_mode == ResearchMode.FOLLOW_UP:
            selected_tools = [FinishTool]
        elif research_mode == ResearchMode.DEEP_RESEARCH:
            # Start with built-in tools
            selected_tools = deepcopy(self.tools)

            if self.config.a2a_server_urls:
                selected_tools.extend([ListRemoteAgents, SendTask])

            # Add search tools, avoiding duplicates
            existing_names = {tool['function']['name'] for tool in selected_tools}
            unique_search_tools = [
                tool
                for tool in self.search_tools
                if tool['function']['name'] not in existing_names
            ]
            selected_tools.extend(unique_search_tools)

            # Add MCP tools, avoiding duplicates
            existing_names = {tool['function']['name'] for tool in selected_tools}
            unique_mcp_tools = [
                tool
                for tool in self.mcp_tools
                if tool['function']['name'] not in existing_names
            ]
            selected_tools.extend(unique_mcp_tools)
        else:
            # For other modes, combine tools and search_tools with deduplication
            selected_tools = deepcopy(self.tools)
            existing_names = {tool['function']['name'] for tool in selected_tools}
            unique_search_tools = [
                tool
                for tool in self.search_tools
                if tool['function']['name'] not in existing_names
            ]
            selected_tools.extend(unique_search_tools)

        logger.debug(f'Selected tools: {selected_tools}')

        # NOTE:only for anthropic model, we need to set the cache_control for the tool list
        if 'claude' in self.llm.config.model and len(selected_tools) > 0:
            # Remove any existing cache_control first
            for tool in selected_tools:
                if 'cache_control' in tool:
                    del tool['cache_control']
            # Add cache_control to last element so it is persistent
            selected_tools[-1]['cache_control'] = {'type': 'ephemeral'}
        return selected_tools

    async def _handle_streaming_response(
        self, streaming_response, tools: list[dict], research_mode: str | None
    ):
        """Handle streaming response - both accumulate in pending_actions AND yield chunks immediately"""
        # Accumulate streaming data
        accumulated_tool_calls = {}  # tool_call_id -> partial tool call data
        index_to_id_map = {}  # index -> tool_call_id mapping
        last_chunk = None
        has_tool_calls = False  # Track if we accumulated any tool calls
        accumulated_content = ''  # Track assistant content

        # For streaming "finish" or "think" function message content
        streaming_function_calls: dict[str, Any] = {}  # tool_call_id -> streaming state
        async for chunk in streaming_response:
            last_chunk = chunk
            logger.debug(f'Streaming chunk: {chunk}')
            delta = chunk.choices[0].delta
            # Handle tool call chunks - ACCUMULATE
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                has_tool_calls = True
                for tool_call_delta in delta.tool_calls:
                    tool_call_id = getattr(tool_call_delta, 'id', None)
                    tool_call_index = getattr(tool_call_delta, 'index', 0)

                    # Determine which tool call to update
                    target_tool_call = None
                    target_id = None

                    if tool_call_id:
                        # Use the provided ID
                        target_id = tool_call_id
                        if target_id not in accumulated_tool_calls:
                            accumulated_tool_calls[target_id] = {
                                'id': target_id,
                                'type': getattr(tool_call_delta, 'type', 'function'),
                                'function': {'name': '', 'arguments': ''},
                            }
                        # Map this index to this ID for future reference
                        index_to_id_map[tool_call_index] = target_id
                        target_tool_call = accumulated_tool_calls[target_id]
                    else:
                        # No ID provided - use index to find existing tool call
                        if tool_call_index in index_to_id_map:
                            # We've seen this index before, use the existing tool call
                            target_id = index_to_id_map[tool_call_index]
                            if target_id not in accumulated_tool_calls:
                                continue
                            target_tool_call = accumulated_tool_calls[target_id]
                        else:
                            # New index without ID - create new tool call
                            target_id = f'tool_call_{tool_call_index}'
                            accumulated_tool_calls[target_id] = {
                                'id': target_id,
                                'type': getattr(tool_call_delta, 'type', 'function'),
                                'function': {'name': '', 'arguments': ''},
                            }
                            index_to_id_map[tool_call_index] = target_id
                            target_tool_call = accumulated_tool_calls[target_id]

                    # Update function name and arguments incrementally
                    if hasattr(tool_call_delta, 'function') and target_tool_call:
                        func_delta = tool_call_delta.function
                        if hasattr(func_delta, 'name') and func_delta.name:
                            target_tool_call['function']['name'] += func_delta.name
                        if hasattr(func_delta, 'arguments') and func_delta.arguments:
                            target_tool_call['function']['arguments'] += (
                                func_delta.arguments
                            )

                            # Check if this is a "finish" or "think" function and stream the message content
                            function_name = target_tool_call['function']['name']
                            if function_name in ['finish']:
                                self._stream_function_message(
                                    target_id,
                                    func_delta.arguments,
                                    streaming_function_calls,
                                    research_mode,
                                )
            else:
                if delta.content:
                    accumulated_content += delta.content

                    # Only set wait_for_response=True if we don't have tool calls to process
                    wait_for_response = not has_tool_calls
                    stream_action = StreamingMessageAction(
                        content=delta.content,
                        wait_for_response=wait_for_response,
                        enable_process_llm=False,
                    )
                    if self.event_stream is not None:
                        self.event_stream.add_event(stream_action, EventSource.AGENT)

        # AFTER streaming is complete, process accumulated data
        if accumulated_content and not has_tool_calls:
            message_action = MessageAction(
                content=accumulated_content,
                wait_for_response=True,
                enable_think=False,
            )
            self.pending_actions.append(message_action)

        # FIRST: Process tool calls (if any)
        if accumulated_tool_calls:
            try:
                from litellm import ModelResponse

                formatted_tool_calls = []
                for tool_call_data in accumulated_tool_calls.values():
                    # Validate that we have complete tool call data
                    # A tool call needs both name and arguments to be valid
                    has_name = tool_call_data['function']['name'].strip()
                    has_args = tool_call_data['function']['arguments'].strip()
                    logger.debug(f'Tool call data: {has_name} {has_args}')
                    if has_name and has_args:
                        formatted_tool_calls.append(
                            {
                                'id': tool_call_data['id'],
                                'type': tool_call_data['type'],
                                'function': {
                                    'name': tool_call_data['function']['name'],
                                    'arguments': tool_call_data['function'][
                                        'arguments'
                                    ],
                                },
                            }
                        )
                    else:
                        logger.warning(f'Incomplete tool call data: {tool_call_data}')
                        logger.warning(
                            f'Has name: {bool(has_name)}, Has args: {bool(has_args)}'
                        )

                if formatted_tool_calls:
                    logger.info(
                        f'Successfully formatted {len(formatted_tool_calls)} tool calls'
                    )
                    # Create mock response with both content and tool calls if available
                    mock_response = ModelResponse(
                        id=last_chunk.id if last_chunk else 'mock-streaming-id',
                        choices=[
                            {
                                'message': {
                                    'role': 'assistant',
                                    'content': accumulated_content
                                    if accumulated_content
                                    else None,
                                    'tool_calls': formatted_tool_calls,
                                },
                                'index': 0,
                                'finish_reason': 'tool_calls',
                            }
                        ],
                    )

                    # Use existing response_to_actions logic
                    actions = codeact_function_calling.response_to_actions(
                        mock_response,
                        self.session_id,
                        self.workspace_mount_path_in_sandbox_store_in_session,
                        tools=tools,
                        enable_think=False,
                    )

                    for action in actions:
                        if isinstance(action, AgentFinishAction):
                            content = ''
                            if action.task_completed == 'partial':
                                content = 'I believe that the task was **completed partially**.'
                            elif action.task_completed == 'false':
                                content = (
                                    'I believe that the task was **not completed**.'
                                )
                            elif action.task_completed == 'true':
                                content = 'I believe that the task was **completed successfully**.'
                            if content and self.event_stream:
                                self.event_stream.add_event(
                                    StreamingMessageAction(
                                        content=content,
                                        wait_for_response=True,
                                        enable_process_llm=False,
                                    ),
                                    EventSource.AGENT,
                                )
                        self.pending_actions.append(action)

            except Exception as e:
                logger.error(f'Error processing accumulated tool calls: {e}')
                # Log the accumulated tool calls for debugging
                # Fallback to simple message action - use regular MessageAction for pending_actions
                fallback_action = MessageAction(
                    content=str(e)
                    or 'Error processing tool calls from streaming response',
                )
                self.pending_actions.append(fallback_action)

    def _stream_function_message(
        self,
        tool_call_id: str,
        arguments_chunk: str,
        streaming_function_calls: dict,
        research_mode: str | None = None,
    ):
        """Stream message content from finish/think function calls as they arrive"""
        # Initialize tracking for this tool call if not exists
        if tool_call_id not in streaming_function_calls:
            streaming_function_calls[tool_call_id] = {
                'buffer': '',
                'msg_start': -1,
                'streamed': 0,
            }

        state = streaming_function_calls[tool_call_id]
        state['buffer'] += arguments_chunk

        # Find message start if not found yet
        if state['msg_start'] == -1:
            # Look for "message" pattern with flexible whitespace
            for pattern in ['"message":', '"message" :', '"message": ', '"message" : ']:
                if pattern in state['buffer']:
                    start = state['buffer'].find(pattern) + len(pattern)
                    # Skip whitespace and find opening quote
                    while (
                        start < len(state['buffer'])
                        and state['buffer'][start].isspace()
                    ):
                        start += 1
                    if start < len(state['buffer']) and state['buffer'][start] == '"':
                        state['msg_start'] = start + 1
                        break

        # Stream message content if we found the start
        if state['msg_start'] != -1:
            content = state['buffer'][state['msg_start'] :]
            end_quote = self._find_unescaped_quote(content)

            if end_quote != -1:
                content = content[:end_quote]

            # Stream new content
            if len(content) > state['streamed']:
                new_content = content[state['streamed'] :]
                safe_content = self._get_safe_content(new_content)
                if safe_content:
                    # dont stream final_thought when we are in follow_up mode
                    if research_mode != ResearchMode.FOLLOW_UP:
                        self._emit_streaming_content(safe_content)
                    state['streamed'] += len(safe_content)

    def _get_safe_content(self, content: str) -> str:
        """Extract content safe to stream (avoid partial escapes)"""
        if not content:
            return ''

        # Don't stream if ends with backslash or incomplete unicode
        if content.endswith('\\'):
            return content[:-1] if len(content) > 1 else ''

        import re

        if re.search(r'\\u[0-9a-fA-F]{0,3}$', content):
            match = re.search(r'(.*?)\\u[0-9a-fA-F]{0,3}$', content)
            return match.group(1) if match else ''

        return content

    def _find_unescaped_quote(self, text: str) -> int:
        """Find first unescaped quote position"""
        for i, char in enumerate(text):
            if char == '"':
                # Count preceding backslashes
                backslashes = 0
                j = i - 1
                while j >= 0 and text[j] == '\\':
                    backslashes += 1
                    j -= 1
                # Even number of backslashes means quote is not escaped
                if backslashes % 2 == 0:
                    return i
        return -1

    def _emit_streaming_content(self, content: str):
        """Emit streaming content through event stream"""
        if content and self.event_stream:
            try:
                import json

                decoded = json.loads(f'"{content}"')
                action = StreamingMessageAction(
                    content=decoded, wait_for_response=False, enable_process_llm=False
                )
                self.event_stream.add_event(action, EventSource.AGENT)
            except json.JSONDecodeError:
                action = StreamingMessageAction(
                    content=content, wait_for_response=False, enable_process_llm=False
                )
                self.event_stream.add_event(action, EventSource.AGENT)

    def step(self, state: State) -> Optional[Action]:
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
        if self.session_id is None:
            self.session_id = state.session_id
        # Continue with pending actions if any
        if self.pending_actions:
            return self.pending_actions.popleft()

        # if we're done, go back
        latest_user_message = state.get_last_user_message()

        if latest_user_message and latest_user_message.content.strip() == '/exit':
            return AgentFinishAction()

        # Condense the events from the state. If we get a view we'll pass those
        # to the conversation manager for processing, but if we get a condensation
        # event we'll just return that instead of an action. The controller will
        # immediately ask the agent to step again with the new view.
        condensed_history: list[Event] = []
        match self.condenser.condensed_history(state):
            case View(events=events):
                condensed_history = events

            case Condensation(action=condensation_action):
                return condensation_action

        logger.info(
            f'Processing {len(condensed_history)} events from a total of {len(state.history)} events'
        )
        research_mode = (
            latest_user_message.mode if latest_user_message is not None else None
        )

        messages = self._get_messages(condensed_history, research_mode=research_mode)
        formatted_messages = self.llm.format_messages_for_llm(messages)
        convert_knowledge_to_list = [
            self.knowledge_base[k] for k in self.knowledge_base
        ]
        # NOTE: This is user's dynamic knowledge base. Do not cache this message, as it will be updated frequently.
        # NOTE: Only cache static large knowledge base that is uploaded by the user (changed rarely).
        if len(convert_knowledge_to_list) > 0:
            formatted_messages.append(
                {
                    'role': 'assistant',
                    'content': [
                        {
                            'type': 'text',
                            'text': "User's Knowledge base is in <knowledge_base></knowledge_base> tag\n",
                        },
                        {
                            'type': 'text',
                            'text': f'<knowledge_base>{json.dumps(convert_knowledge_to_list)}</knowledge_base>',
                        },
                        {
                            'type': 'text',
                            'text': "Use it for user info's reference if needed.",
                        },
                    ],
                }
            )
        current_date = datetime.now().strftime('%Y-%m-%d')
        formatted_messages.append(
            {
                'role': 'assistant',
                'content': [
                    {
                        'type': 'text',
                        'text': f'Current date is {current_date}. Ignore anything that contradicts this.',
                    },
                ],
            }
        )
        params: dict = {
            'messages': formatted_messages,
        }
        params['extra_body'] = {'metadata': state.to_llm_metadata(agent_name=self.name)}
        # if chat mode, we need to use the search tools
        params['tools'] = self._select_tools_based_on_mode(research_mode)
        params['tools'] = check_tools(params['tools'], self.llm.config)
        if self.enable_streaming:
            params['stream_options'] = {'include_usage': True}
        logger.info(f'Messages: {messages}')
        last_message = messages[-1]
        response = None
        if (
            last_message.role == 'user'
            and self.config.enable_llm_router
            and self.config.llm_router_infer_url is not None
            and self.routing_llms is not None
            and self.routing_llms['simple'] is not None
        ):
            content = '\n'.join(
                [
                    msg.text
                    for msg in last_message.content
                    if isinstance(msg, TextContent)
                ]
            )
            text_input = 'Prompt: ' + content
            body = {
                'inputs': [
                    {
                        'name': 'INPUT',
                        'shape': [1, 1],
                        'datatype': 'BYTES',
                        'data': [text_input],
                    }
                ]
            }
            logger.debug(f'Body: {body}')
            headers = {'Content-Type': 'application/json'}
            result = request(
                'POST',
                self.config.llm_router_infer_url,
                data=json.dumps(body),
                headers=headers,
            )
            res = result.json()
            logger.debug(f'Result from classifier: {res}')
            complexity_score = res['outputs'][0]['data'][0]
            logger.debug(f'Complexity score: {complexity_score}')
            if complexity_score > 0.3:
                response = (
                    self.llm.completion(**params)
                    if not self.streaming_llm
                    else self.streaming_llm.async_streaming_completion(**params)
                )
            else:
                response = (
                    self.routing_llms['simple'].completion(**params)
                    if not self.streaming_routing_llm
                    else self.streaming_routing_llm.async_streaming_completion(**params)
                )
        else:
            # Use streaming response
            response = (
                self.llm.completion(**params)
                if not self.streaming_llm
                else self.streaming_llm.async_streaming_completion(**params)
            )
            # Process streaming response and populate pending_actions
        if self.enable_streaming:
            call_async_from_sync(
                self._handle_streaming_response,
                15,
                response,
                params['tools'],
                research_mode,
            )
            if self.pending_actions:
                logger.info(
                    f'Returning first of {len(self.pending_actions)} pending actions from streaming'
                )
                return self.pending_actions.popleft()
        else:
            actions = codeact_function_calling.response_to_actions(
                response,
                state.session_id,
                self.workspace_mount_path_in_sandbox_store_in_session,
                tools=params['tools'],
            )
            logger.debug(f'Actions after response_to_actions: {actions}')
            for action in actions:
                self.pending_actions.append(action)
            return self.pending_actions.popleft()
        return None

    def _get_messages(
        self, events: list[Event], research_mode: str | None = None
    ) -> list[Message]:
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
            events: The list of events to convert to messages

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
        agent_infos = (
            self.a2a_manager.list_remote_agents() if self.a2a_manager else None
        )

        # Use ConversationMemory to process initial messages
        # switch mode and initial messages

        messages = self.conversation_memory.process_initial_messages(
            with_caching=self.llm.is_caching_prompt_active(),
            agent_infos=agent_infos,
        )
        if research_mode == ResearchMode.FOLLOW_UP:
            messages = self.conversation_memory.process_initial_followup_message(
                with_caching=self.llm.is_caching_prompt_active(),
            )
        elif research_mode is None or research_mode == ResearchMode.CHAT:
            messages = self.conversation_memory.process_initial_chatmode_message(
                with_caching=self.llm.is_caching_prompt_active(),
                search_tools=[
                    {
                        'name': tool['function']['name'],
                        'description': tool['function']['description'],
                    }
                    for tool in self.search_tools
                ],
            )
        # Use ConversationMemory to process events
        messages = self.conversation_memory.process_events(
            condensed_history=events,
            initial_messages=messages,
            max_message_chars=self.llm.config.max_message_chars,
            vision_is_active=self.llm.vision_is_active(),
        )

        messages = self._enhance_messages(messages)

        if self.llm.is_caching_prompt_active():
            self.conversation_memory.apply_prompt_caching(messages)

        return messages

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
        prev_role = None

        for msg in messages:
            if msg.role == 'user' and not is_first_message_handled:
                is_first_message_handled = True
                # compose the first user message with examples
                self.prompt_manager.add_examples_to_initial_message(
                    msg, self.session_id
                )

            elif msg.role == 'user':
                # Add double newline between consecutive user messages
                if prev_role == 'user' and len(msg.content) > 0:
                    # Find the first TextContent in the message to add newlines
                    for content_item in msg.content:
                        if isinstance(content_item, TextContent):
                            # If the previous message was also from a user, prepend two newlines to ensure separation
                            content_item.text = '\n\n' + content_item.text
                            break

            results.append(msg)
            prev_role = msg.role

        return results
