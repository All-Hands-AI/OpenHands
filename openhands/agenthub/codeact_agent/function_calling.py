"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json

from litellm import (
    ModelResponse,
)

from openhands.agenthub.codeact_agent.llm_diff_parser import (
    DiffBlock,
    parse_llm_response_for_diffs,
)
from openhands.agenthub.codeact_agent.tools import (
    BrowserTool,
    FinishTool,
    IPythonTool,
    ListDirectoryTool,
    LLMBasedFileEditTool,
    ThinkTool,
    UndoEditTool,
    ViewFileTool,
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
    response: ModelResponse, mcp_tool_names: list[str] | None = None, is_llm_diff_enabled: bool = False
) -> list[Action]:
    """
    Parses the LLM response and converts it into a list of OpenHands Actions.

    The function handles two main types of responses:
    1. Tool calls - When the LLM response contains function calls
    2. Diff blocks - When is_llm_diff_enabled=True and the response contains code diffs

    For tool calls, it converts each function call into a corresponding Action:
    - execute_bash -> CmdRunAction
    - execute_ipython_cell -> IPythonRunCellAction
    - browser -> BrowseInteractiveAction
    - web_read -> BrowseURLAction
    - str_replace_editor -> FileEditAction/FileReadAction
    - think -> AgentThinkAction
    - finish -> AgentFinishAction
    - delegate_to_browsing_agent -> AgentDelegateAction

    For diff blocks (when is_llm_diff_enabled=True), it parses blocks in the format:
    ```language
    filename.ext
    <<<<<<< SEARCH
    old code
    =======
    new code
    >>>>>>> REPLACE
    ```
    Each diff block is converted to a FileEditAction with:
    - path = filename
    - search = old code
    - replace = new code
    - impl_source = FileEditSource.LLM_DIFF

    Examples:
        # Tool call response
        response = {
            "tool_calls": [{
                "function": {
                    "name": "execute_bash",
                    "arguments": {"command": "ls", "is_input": "false"}
                }
            }]
        }
        -> [CmdRunAction(command="ls", is_input=False)]

        # Diff block response
        response = {
            "content": '''
            ```python
            app.py
            <<<<<<< SEARCH
            old_code
            =======
            new_code
            >>>>>>> REPLACE
            ```
            '''
        }
        -> [FileEditAction(path="app.py", search="old_code", replace="new_code")]

    Args:
        response: The ModelResponse from the LLM.
        mcp_tool_names: Optional list of MCP tool names to handle.
        is_llm_diff_enabled: If True, will attempt to parse diff blocks from message
                           content if no tool calls exist. Defaults to False.

    Returns:
        A list of Action objects.

    Note:
        - If both tool calls and diff blocks exist, tool calls take precedence
        - Message content outside of tool calls/diff blocks becomes MessageAction
        - At least one action is always returned (AgentThinkAction as fallback)
    """
    all_actions: list[Action] = []
    parsed_llm_diff_actions: list[Action] = []
    tool_call_actions: list[Action] = []
    message_content: str = ''
    diff_parse_error: Exception | None = None
    action: Action

    assert len(response.choices) == 1, 'Only one choice is supported for now'
    choice = response.choices[0]
    assistant_msg = choice.message

    # 1. Extract message content
    if isinstance(assistant_msg.content, str):
        message_content = assistant_msg.content
    elif isinstance(assistant_msg.content, list):
        for msg in assistant_msg.content:
            if msg['type'] == 'text':
                message_content += msg['text']

    # 2. Try parsing diff blocks if enabled and content exists
    if is_llm_diff_enabled and message_content:
        logger.debug('LLM Diff mode enabled, attempting to parse response content.')
        try:
            # Call the updated parser, expecting list[DiffBlock]
            parsed_blocks: list[DiffBlock] = parse_llm_response_for_diffs(
                message_content
            )

            if parsed_blocks:  # Check if the list is not empty
                logger.info(
                    f'Parsed {len(parsed_blocks)} diff blocks from LLM response.'
                )
                # Create FileEditActions from the DiffBlock objects
                for block in parsed_blocks:
                    action = FileEditAction(
                        path=block.filename,
                        search=block.search,
                        replace=block.replace,
                        impl_source=FileEditSource.LLM_DIFF,
                    )
                    parsed_llm_diff_actions.append(action)

        except ValueError as e:
            logger.error(f'Error parsing LLM diff blocks: {e}')
            diff_parse_error = e  # Store error for potential later use
        except Exception as e:
            logger.error(
                f'Unexpected error during LLM diff parsing: {e}', exc_info=True
            )
            diff_parse_error = e  # Store error

    # 3. Process tool calls if they exist
    tool_calls_exist = hasattr(assistant_msg, 'tool_calls') and assistant_msg.tool_calls
    if tool_calls_exist:
        # Process each tool call
        for i, tool_call in enumerate(assistant_msg.tool_calls):
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
            # New Utility Tools (Routing to OH_ACI)
            # ================================================
            elif tool_call.function.name == ViewFileTool['function']['name']:
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                action = FileReadAction(
                    path=arguments['path'],
                    impl_source=FileReadSource.OH_ACI,
                    view_range=arguments.get('view_range', None),
                )
            elif tool_call.function.name == ListDirectoryTool['function']['name']:
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                action = FileReadAction(
                    path=arguments['path'],
                    impl_source=FileReadSource.OH_ACI,
                    # view_range is not applicable for directories
                )
            elif tool_call.function.name == UndoEditTool['function']['name']:
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                action = FileEditAction(
                    path=arguments['path'],
                    command='undo_edit',
                    impl_source=FileEditSource.OH_ACI,
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

            # Add metadata for tool calling
            action.tool_call_metadata = ToolCallMetadata(
                tool_call_id=tool_call.id,
                function_name=tool_call.function.name,
                model_response=response,
                total_calls_in_response=len(assistant_msg.tool_calls),
            )
            tool_call_actions.append(action)

    # 4. Combine actions: diffs first (if any), then tool calls (if any)
    all_actions.extend(parsed_llm_diff_actions)
    all_actions.extend(tool_call_actions)

    # 5. Handle the case where no actions were generated (neither diffs nor tool calls)
    if not all_actions:
        # If there was a diff parsing error, report it (even if no blocks were parsed)
        if diff_parse_error:
            all_actions.append(
                MessageAction(
                    content=f'[Error parsing diff blocks: {diff_parse_error}]\nOriginal Content:\n{message_content}',
                    wait_for_response=True,
                )
            )
        # Otherwise, treat as a regular message if content exists
        elif message_content:
            all_actions.append(
                MessageAction(
                    content=message_content,
                    wait_for_response=True,
                )
            )
        # If no actions AND no content, add a default Think action
        else:
            logger.warning(
                f'No actions generated and no message content for response: {response.id}'
            )
            all_actions.append(
                AgentThinkAction(
                    thought='[No actionable content or tool calls found in response]'
                )
            )

    # If actions *were* generated, determine and apply thought
    else:
        # 6. Determine contextual thought and apply to the first non-AgentThinkAction
        contextual_thought = message_content.strip() if message_content else None
        if contextual_thought:
            for i, action in enumerate(all_actions):
                if not isinstance(action, AgentThinkAction):
                    all_actions[i] = combine_thought(action, contextual_thought)
                    break  # Apply thought only to the first eligible action

    # 7. Add response id to all actions
    for action in all_actions:
        action.response_id = response.id

    # 8. Final check (ensure at least one action exists)
    if not all_actions:
        # This case should ideally be handled by step 5, but as a safeguard:
        logger.error(
            f'CRITICAL: No actions generated for response {response.id} after all checks.'
        )
        # Create a default Think action if somehow we ended up with no actions
        all_actions.append(
            AgentThinkAction(thought='[Critical Error: Failed to generate any action]')
        )
        if all_actions[0]:
            all_actions[0].response_id = response.id

    return all_actions
