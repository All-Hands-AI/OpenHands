"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json

from litellm import (
    ChatCompletionToolParam,
    ModelResponse,
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
    WebReadTool,
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
from openhands.agenthub.codeact_agent.llm_diff_parser import (
    parse_llm_response_for_diffs,
)
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.mcp import McpAction
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.tool import ToolCallMetadata
from openhands.llm import LLM
from openhands.mcp import MCPClientTool


def combine_thought(action: Action, thought: str) -> Action:
    if not hasattr(action, 'thought'):
        return action
    if thought and action.thought:
        action.thought = f'{thought}\n{action.thought}'
    elif thought:
        action.thought = thought
    return action


def response_to_actions(response: ModelResponse, is_llm_diff_enabled: bool = False) -> list[Action]:
    """
    Parses the LLM response and converts it into a list of OpenHands Actions.

    Args:
        response: The ModelResponse from the LLM.
        is_llm_diff_enabled: If True, will attempt to parse diff blocks from message
                             content if no tool calls exist. Defaults to False.

    Returns:
        A list of Action objects.
    """
    all_actions: list[Action] = []
    parsed_llm_diff_actions: list[Action] = []
    tool_call_actions: list[Action] = []
    thought_from_diff: str | None = None
    thought_from_tool_content: str | None = None
    message_content: str = ''
    diff_parse_error: Exception | None = None

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
            # TODO: Pass valid_fnames if available from context/summary?
            parsed_blocks, first_block_start_idx, last_block_end_idx = parse_llm_response_for_diffs(message_content)
            if parsed_blocks:
                logger.info(f'Parsed {len(parsed_blocks)} diff blocks from LLM response.')
                # Extract thought based on the start index
                if first_block_start_idx != -1:
                    thought_from_diff = message_content[:first_block_start_idx].strip()
                else:
                    logger.warning("Could not determine start index of the first diff block. Using empty thought.")
                    # thought_from_diff remains None

                for i, (filename, search, replace) in enumerate(parsed_blocks):
                    action = FileEditAction(
                        path=filename,
                        search=search,
                        replace=replace,
                        impl_source=FileEditSource.LLM_DIFF,
                    )
                    parsed_llm_diff_actions.append(action)

        except ValueError as e:
            logger.error(f'Error parsing LLM diff blocks: {e}')
            diff_parse_error = e # Store error for potential later use
        except Exception as e:
             logger.error(f'Unexpected error during LLM diff parsing: {e}', exc_info=True)
             diff_parse_error = e # Store error

    # 3. Process tool calls if they exist
    if hasattr(assistant_msg, 'tool_calls') and assistant_msg.tool_calls:
        # If we haven't extracted thought from diff blocks yet, extract it now from content
        # This happens if diff parsing was disabled, failed, or found no blocks
        if thought_from_diff is None and not parsed_llm_diff_actions:
             if isinstance(assistant_msg.content, str):
                 thought_from_tool_content = assistant_msg.content.strip() # Use the raw content as thought
             elif isinstance(assistant_msg.content, list):
                 temp_thought = ''
                 for msg in assistant_msg.content:
                     if msg['type'] == 'text':
                         temp_thought += msg['text']
                 thought_from_tool_content = temp_thought.strip()

        # Process each tool call
        for i, tool_call in enumerate(assistant_msg.tool_calls):
            action: Action
            logger.debug(f'Tool call in function_calling.py: {tool_call}')
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.decoder.JSONDecodeError as e:
                raise RuntimeError(
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
                    action = FileEditAction(
                        path=path,
                        command=command,
                        impl_source=FileEditSource.OH_ACI,
                    **other_kwargs,
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
            # WebReadTool (simplified browsing)
            # ================================================
            elif tool_call.function.name == WebReadTool['function']['name']:
                if 'url' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "url" in tool call {tool_call.function.name}'
                    )
                action = BrowseURLAction(url=arguments['url'])

            # ================================================
            # McpAction (MCP)
            # ================================================
            elif tool_call.function.name.endswith(MCPClientTool.postfix()):
                action = McpAction(
                    name=tool_call.function.name.rstrip(MCPClientTool.postfix()),
                    arguments=tool_call.function.arguments,
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

    # 4. Combine actions: diffs first, then tool calls
    all_actions.extend(parsed_llm_diff_actions)
    all_actions.extend(tool_call_actions)

    # 5. Handle the case where no actions were generated
    if not all_actions:
        # If there was a diff parsing error, report it
        if diff_parse_error:
             all_actions.append(
                 MessageAction(
                     content=message_content + f'\n\n[Error parsing diff blocks: {diff_parse_error}]',
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
            logger.warning(f"No actions generated and no message content for response: {response.id}")
            all_actions.append(AgentThinkAction(thought="[No actionable content or tool calls found in response]"))


    # 6. Determine contextual thought and apply to the first non-AgentThinkAction
    contextual_thought = thought_from_diff if thought_from_diff is not None else thought_from_tool_content
    thought_applied = False
    if contextual_thought:
        for i, action in enumerate(all_actions):
            if not isinstance(action, AgentThinkAction):
                all_actions[i] = combine_thought(action, contextual_thought)
                thought_applied = True
                break # Apply thought only to the first eligible action

    # 7. Add response id to all actions
    for action in all_actions:
        action.response_id = response.id

    # 8. Final check (ensure at least one action exists)
    if not all_actions:
         # This case should ideally be handled by step 5, but as a safeguard:
         logger.error(f"CRITICAL: No actions generated for response {response.id} after all checks.")
         all_actions.append(AgentThinkAction(thought="[Critical Error: Failed to generate any action]"))
         if all_actions[0]: all_actions[0].response_id = response.id


    return all_actions


from openhands.core.config import AgentConfig

def get_tools(
    config: AgentConfig,
    llm: LLM | None = None,
) -> list[ChatCompletionToolParam]:
    # Extract flags from config
    enable_browsing = config.enable_browsing
    enable_llm_editor = config.enable_llm_editor
    enable_llm_diff = config.enable_llm_diff
    enable_jupyter = config.enable_jupyter

    SIMPLIFIED_TOOL_DESCRIPTION_LLM_SUBSTRS = ['gpt-', 'o3', 'o1']

    use_simplified_tool_desc = False
    if llm is not None:
        use_simplified_tool_desc = any(
            model_substr in llm.config.model
            for model_substr in SIMPLIFIED_TOOL_DESCRIPTION_LLM_SUBSTRS
        )

    tools = [
        create_cmd_run_tool(use_simplified_description=use_simplified_tool_desc),
        ThinkTool,
        FinishTool,
    ]
    if enable_browsing:
        tools.append(WebReadTool)
        tools.append(BrowserTool)
    if enable_jupyter:
        tools.append(IPythonTool)

    # Determine which editor tool(s) and utility tools to add based on config
    if enable_llm_diff:
        # Use LLM Diff mode:
        #  - LLM generates diffs in text, only non-edit tools available
        #  - No UndoEditTool
        tools.append(ViewFileTool)
        tools.append(ListDirectoryTool)
        # NO EDITING TOOLS (LLMBasedFileEditTool, str_replace_editor)
        # NO UndoEditTool
    elif enable_llm_editor:
        # Use LLM-based editor tool + separate utils (NO Undo)
        tools.append(LLMBasedFileEditTool)
        tools.append(ViewFileTool)
        tools.append(ListDirectoryTool)
        # No UndoEditTool here
    else:
        # Fallback to the complete str_replace_editor (includes view, list, undo)
        tools.append(
            create_str_replace_editor_tool(
                use_simplified_description=use_simplified_tool_desc
            )
        )

    return tools
