"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json

from litellm import (
    ModelResponse,
)

from openhands.agenthub.codeact_agent.tools import (
    BrowserTool,
    FinishTool,
    IPythonTool,
    LLMBasedFileEditTool,
    ThinkTool,
    create_cmd_run_tool,
    create_str_replace_editor_tool,
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
    FunctionCallValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentThinkAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.action.mcp import MCPAction
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.tool import ToolCallMetadata


def combine_thought(action: Action, thought: str) -> Action:
    if not hasattr(action, 'thought'):
        return action
    if thought and action.thought:
        action.thought = f'{thought}\n{action.thought}'
    elif thought:
        action.thought = thought
    return action


def response_to_actions(
    response: ModelResponse, mcp_tool_names: list[str] | None = None
) -> list[Action]:
    actions: list[Action] = []
    assert len(response.choices) == 1, 'Only one choice is supported for now'
    choice = response.choices[0]
    assistant_msg = choice.message
    if hasattr(assistant_msg, 'tool_calls') and assistant_msg.tool_calls:
        # Check if there's assistant_msg.content. If so, add it to the thought
        thought = ''
        if isinstance(assistant_msg.content, str):
            thought = assistant_msg.content
        elif isinstance(assistant_msg.content, list):
            for msg in assistant_msg.content:
                if msg['type'] == 'text':
                    thought += msg['text']

        # Process each tool call to OpenHands action
        for i, tool_call in enumerate(assistant_msg.tool_calls):
            action: Action
            logger.debug(f'Tool call in function_calling.py: {tool_call}')
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.decoder.JSONDecodeError as e:
                raise FunctionCallValidationError(
                    f'Failed to parse tool call arguments: {tool_call.function.arguments}'
                ) from e

            # ================================================
            # CmdRunTool (Bash)
            # ================================================

            if tool_call.function.name == create_cmd_run_tool()['function']['name']:
                if 'command' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "command" in tool call {tool_call.function.name}'
                    )
                # convert is_input to boolean
                is_input = arguments.get('is_input', 'false') == 'true'
                action = CmdRunAction(command=arguments['command'], is_input=is_input)

                # Set hard timeout if provided
                if 'timeout' in arguments:
                    try:
                        action.set_hard_timeout(float(arguments['timeout']))
                    except ValueError as e:
                        raise FunctionCallValidationError(
                            f"Invalid float passed to 'timeout' argument: {arguments['timeout']}"
                        ) from e

            # ================================================
            # IPythonTool (Jupyter)
            # ================================================
            elif tool_call.function.name == IPythonTool['function']['name']:
                if 'code' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "code" in tool call {tool_call.function.name}'
                    )
                action = IPythonRunCellAction(code=arguments['code'])
            elif tool_call.function.name == 'delegate_to_browsing_agent':
                action = AgentDelegateAction(
                    agent='BrowsingAgent',
                    inputs=arguments,
                )

            # ================================================
            # AgentFinishAction
            # ================================================
            elif tool_call.function.name == FinishTool['function']['name']:
                action = AgentFinishAction(
                    final_thought=arguments.get('message', ''),
                    task_completed=arguments.get('task_completed', None),
                )

            # ================================================
            # LLMBasedFileEditTool (LLM-based file editor, deprecated)
            # ================================================
            elif tool_call.function.name == LLMBasedFileEditTool['function']['name']:
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                if 'content' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "content" in tool call {tool_call.function.name}'
                    )
                action = FileEditAction(
                    path=arguments['path'],
                    content=arguments['content'],
                    start=arguments.get('start', 1),
                    end=arguments.get('end', -1),
                )
            elif (
                tool_call.function.name
                == create_str_replace_editor_tool()['function']['name']
            ):
                if 'command' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "command" in tool call {tool_call.function.name}'
                    )
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                path = arguments['path']
                command = arguments['command']
                other_kwargs = {
                    k: v for k, v in arguments.items() if k not in ['command', 'path']
                }

                if command == 'view':
                    action = FileReadAction(
                        path=path,
                        impl_source=FileReadSource.OH_ACI,
                        view_range=other_kwargs.get('view_range', None),
                    )
                else:
                    if 'view_range' in other_kwargs:
                        # Remove view_range from other_kwargs since it is not needed for FileEditAction
                        other_kwargs.pop('view_range')

                    # Filter out unexpected arguments
                    valid_kwargs = {}
                    # Get valid parameters from the str_replace_editor tool definition
                    str_replace_editor_tool = create_str_replace_editor_tool()
                    valid_params = set(
                        str_replace_editor_tool['function']['parameters'][
                            'properties'
                        ].keys()
                    )
                    for key, value in other_kwargs.items():
                        if key in valid_params:
                            valid_kwargs[key] = value
                        else:
                            raise FunctionCallValidationError(
                                f'Unexpected argument {key} in tool call {tool_call.function.name}. Allowed arguments are: {valid_params}'
                            )

                    action = FileEditAction(
                        path=path,
                        command=command,
                        impl_source=FileEditSource.OH_ACI,
                        **valid_kwargs,
                    )
            # ================================================
            # AgentThinkAction
            # ================================================
            elif tool_call.function.name == ThinkTool['function']['name']:
                action = AgentThinkAction(thought=arguments.get('thought', ''))

            # ================================================
            # BrowserTool
            # ================================================
            elif tool_call.function.name == BrowserTool['function']['name']:
                if 'code' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "code" in tool call {tool_call.function.name}'
                    )
                action = BrowseInteractiveAction(browser_actions=arguments['code'])

            # ================================================
            # MCPAction (MCP)
            # ================================================
            elif mcp_tool_names and tool_call.function.name in mcp_tool_names:
                action = MCPAction(
                    name=tool_call.function.name,
                    arguments=arguments,
                )
            else:
                raise FunctionCallNotExistsError(
                    f'Tool {tool_call.function.name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
                )

            # We only add thought to the first action
            if i == 0:
                action = combine_thought(action, thought)
            # Add metadata for tool calling
            action.tool_call_metadata = ToolCallMetadata(
                tool_call_id=tool_call.id,
                function_name=tool_call.function.name,
                model_response=response,
                total_calls_in_response=len(assistant_msg.tool_calls),
            )
            actions.append(action)
    else:
        actions.append(
            MessageAction(
                content=str(assistant_msg.content) if assistant_msg.content else '',
                wait_for_response=True,
            )
        )

    # Add response id to actions
    # This will ensure we can match both actions without tool calls (e.g. MessageAction)
    # and actions with tool calls (e.g. CmdRunAction, IPythonRunCellAction, etc.)
    # with the token usage data
    for action in actions:
        action.response_id = response.id

    assert len(actions) >= 1
    return actions
