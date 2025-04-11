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
    FencedDiffEditTool,
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
from openhands.events.event import FileEditSource, FileReadSource
from openhands.events.tool import ToolCallMetadata
from openhands.llm import LLM


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
            # FencedDiffEditTool (Aider-style SEARCH/REPLACE)
            # ================================================
            elif tool_call.function.name == FencedDiffEditTool['function']['name']:
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                if 'search' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "search" in tool call {tool_call.function.name}'
                    )
                if 'replace' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "replace" in tool call {tool_call.function.name}'
                    )
                action = FileEditAction(
                    path=arguments['path'],
                    search=arguments['search'],
                    replace=arguments['replace'],
                    impl_source=FileEditSource.FENCED_DIFF,
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
        # No tool calls
        message_content = str(assistant_msg.content) if assistant_msg.content else ''
        parsed_llm_diff_actions = []

        # Check for LLM Diff mode ONLY if the flag is set
        if is_llm_diff_enabled:
            logger.debug('LLM Diff mode enabled, attempting to parse response content.')
            try:
                # TODO: Pass valid_fnames if available from context/summary?
                # The parser now returns the blocks and the start/end indices
                parsed_blocks, first_block_start_idx, last_block_end_idx = parse_llm_response_for_diffs(message_content)

                if parsed_blocks:
                    logger.info(f'Parsed {len(parsed_blocks)} diff blocks from LLM response.')

                    # Extract thought based on the start index found by the parser
                    if first_block_start_idx != -1:
                        thought = message_content[:first_block_start_idx].strip()
                    else:
                        # Fallback: If parser couldn't find the start fence,
                        # use the whole content as thought.
                        # This might happen if the response starts *immediately* with a block
                        # or if formatting is unexpected.
                        logger.warning("Could not determine start index of the first diff block. Using full message content as thought.")
                        thought = message_content.strip()

                    for i, (filename, search, replace) in enumerate(parsed_blocks):
                        action = FileEditAction(
                            path=filename,
                            search=search,
                            replace=replace,
                            impl_source=FileEditSource.LLM_DIFF,
                        )
                        # Only add original thought to the *first* action derived from this response
                        if i == 0 and not parsed_llm_diff_actions: # If no AgentThinkAction was added
                             action = combine_thought(action, thought)

                        parsed_llm_diff_actions.append(action)

            except ValueError as e:
                logger.error(f'Error parsing LLM diff blocks: {e}')
                # If parsing fails, clear any partially parsed actions and fall back to MessageAction
                parsed_llm_diff_actions = [
                    MessageAction(
                        content=message_content + f'\n\n[Error parsing diff blocks: {e}]',
                        wait_for_response=True,
                    )
                ]
            except Exception as e:
                 logger.error(f'Unexpected error during LLM diff parsing: {e}', exc_info=True)
                 parsed_llm_diff_actions = [
                    MessageAction(
                        content=message_content + f'\n\n[Unexpected error parsing diff blocks: {e}]',
                        wait_for_response=True,
                    )
                 ]


        # If LLM Diff parsing resulted in actions, use them
        if parsed_llm_diff_actions:
            actions.extend(parsed_llm_diff_actions)
        else:
             # Otherwise (LLM Diff disabled, or enabled but no blocks found/error occurred without fallback),
             # treat as a regular message action.
            if not any(isinstance(a, MessageAction) for a in parsed_llm_diff_actions): # Avoid double message on error
                actions.append(
                    MessageAction(
                        content=message_content,
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


from openhands.core.config import AgentConfig

def get_tools(
    config: AgentConfig,
    llm: LLM | None = None,
) -> list[ChatCompletionToolParam]:
    # Extract flags from config
    codeact_enable_browsing = config.codeact_enable_browsing
    codeact_enable_llm_editor = config.codeact_enable_llm_editor
    codeact_enable_fenced_diff = config.codeact_enable_fenced_diff
    codeact_enable_llm_diff = config.codeact_enable_llm_diff
    codeact_enable_jupyter = config.codeact_enable_jupyter

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
    if codeact_enable_browsing:
        tools.append(WebReadTool)
        tools.append(BrowserTool)
    if codeact_enable_jupyter:
        tools.append(IPythonTool)

    # Determine which editor tool(s) and utility tools to add based on config
    if codeact_enable_llm_diff:
        # Use LLM Diff mode:
        #  - LLM generates diffs in text, only non-edit tools available
        #  - No UndoEditTool
        tools.append(ViewFileTool)
        tools.append(ListDirectoryTool)
        # NO EDITING TOOLS (FencedDiffEditTool, LLMBasedFileEditTool, str_replace_editor)
        # NO UndoEditTool
    elif codeact_enable_fenced_diff:
        # Use Fenced editor tool + separate utils (including Undo)
        tools.append(FencedDiffEditTool)
        tools.append(ViewFileTool)
        tools.append(ListDirectoryTool)
        tools.append(UndoEditTool)
    elif codeact_enable_llm_editor:
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
