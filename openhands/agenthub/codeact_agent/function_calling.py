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
    LLMBasedFileEditTool,
    ThinkTool,
    WebReadTool,
    create_cmd_run_tool,
    create_str_replace_editor_tool,
)
from openhands.core.exceptions import (
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
    McpAction,
    MessageAction,
)
from openhands.events.action.a2a_action import (
    A2AListRemoteAgentsAction,
    A2ASendTaskAction,
)
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


def _validate_required_args(
    tool_name: str, arguments: dict, required_args: list[str]
) -> None:
    """Validate that required arguments are present in tool call arguments."""
    for arg in required_args:
        if arg not in arguments:
            raise FunctionCallValidationError(
                f'Missing required argument "{arg}" in tool call {tool_name}'
            )


def _process_path_with_session(
    path: str, sid: str | None, workspace_mount_path_in_sandbox_store_in_session: bool
) -> str:
    """Process file path with session ID if needed."""
    if (
        sid is not None
        and sid != ''
        and sid not in path
        and workspace_mount_path_in_sandbox_store_in_session
    ):
        processed_path = put_session_id_in_path(path, sid)
        if processed_path == '':
            raise FunctionCallValidationError(
                f'Invalid path: {processed_path}. Original path: {path}. Please provide a valid path.'
            )
        return processed_path
    return path


def _parse_builtin_tool(
    tool_name: str,
    arguments: dict,
    sid: str | None,
    workspace_mount_path_in_sandbox_store_in_session: bool,
    enable_think: bool,
) -> Action:
    """Parse built-in tool calls into actions."""
    # CmdRunTool (Bash)
    if tool_name == create_cmd_run_tool()['function']['name']:
        _validate_required_args(tool_name, arguments, ['command'])
        is_input = arguments.get('is_input', 'false') == 'true'
        return CmdRunAction(command=arguments['command'], is_input=is_input)

    # IPythonTool (Jupyter)
    elif tool_name == IPythonTool['function']['name']:
        _validate_required_args(tool_name, arguments, ['code'])
        return IPythonRunCellAction(code=arguments['code'])

    # Agent delegation
    elif tool_name == 'delegate_to_browsing_agent':
        return AgentDelegateAction(agent='BrowsingAgent', inputs=arguments)

    # FinishTool
    elif tool_name == FinishTool['function']['name']:
        logger.debug(f'FinishTool: {arguments}')
        return AgentFinishAction(
            final_thought=arguments.get('message', ''),
            task_completed=arguments.get('task_completed', None),
            enable_think=enable_think,
        )

    # LLMBasedFileEditTool (deprecated)
    elif tool_name == LLMBasedFileEditTool['function']['name']:
        _validate_required_args(tool_name, arguments, ['path', 'content'])
        path = _process_path_with_session(
            arguments['path'], sid, workspace_mount_path_in_sandbox_store_in_session
        )
        return FileEditAction(
            path=path,
            content=arguments['content'],
            start=arguments.get('start', 1),
            end=arguments.get('end', -1),
        )

    # String replace editor tool
    elif tool_name == create_str_replace_editor_tool()['function']['name']:
        _validate_required_args(tool_name, arguments, ['command', 'path'])
        path = _process_path_with_session(
            arguments['path'], sid, workspace_mount_path_in_sandbox_store_in_session
        )
        command = arguments['command']
        other_kwargs = {
            k: v for k, v in arguments.items() if k not in ['command', 'path']
        }

        if command == 'view':
            return FileReadAction(
                path=path,
                impl_source=FileReadSource.OH_ACI,
                view_range=other_kwargs.get('view_range', None),
            )
        else:
            other_kwargs.pop('view_range', None)  # Remove view_range for FileEditAction
            return FileEditAction(
                path=path,
                command=command,
                impl_source=FileEditSource.OH_ACI,
                **other_kwargs,
            )

    # ThinkTool
    elif tool_name == ThinkTool['function']['name']:
        return AgentThinkAction(thought=arguments.get('thought', ''))

    # BrowserTool
    elif tool_name == BrowserTool['function']['name']:
        _validate_required_args(tool_name, arguments, ['code'])
        return BrowseInteractiveAction(browser_actions=arguments['code'])

    # WebReadTool
    elif tool_name == WebReadTool['function']['name']:
        _validate_required_args(tool_name, arguments, ['url'])
        return BrowseURLAction(url=arguments['url'])

    return AgentThinkAction(
        thought=f'Tool {tool_name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
    )


built_in_tools = {
    create_cmd_run_tool()['function']['name'],
    IPythonTool['function']['name'],
    'delegate_to_browsing_agent',
    FinishTool['function']['name'],
    LLMBasedFileEditTool['function']['name'],
    create_str_replace_editor_tool()['function']['name'],
    ThinkTool['function']['name'],
    BrowserTool['function']['name'],
    WebReadTool['function']['name'],
}


def _parse_tool_call(
    tool_call,
    sid: str | None,
    workspace_mount_path_in_sandbox_store_in_session: bool,
    tools: list[dict] | None,
    enable_think: bool,
) -> Action:
    """Parse a single tool call into an action."""
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.decoder.JSONDecodeError as e:
        raise RuntimeError(
            f'Failed to parse tool call arguments: {tool_call.function.arguments}'
        ) from e

    tool_name = tool_call.function.name
    logger.info(f'Tool call in function_calling.py: {tool_name}')

    # Handle MCP tools
    if tool_name.endswith(MCPClientTool.postfix()):
        original_action_name = tool_name.replace(MCPClientTool.postfix(), '')
        logger.info(f'Original action name: {original_action_name}')

        # Check if MCP tool is available
        tool_found = any(
            tool.get('function', {}).get('name') == tool_name for tool in tools or []
        )

        if tool_found:
            # Handle MCP tool
            if 'pyodide' in original_action_name:
                arguments['sessionId'] = (
                    sid  # Always use session ID for deterministic results
                )
            return McpAction(
                name=original_action_name,
                arguments=json.dumps(arguments),
            )
        else:
            # Check if original action name matches a built-in tool

            if original_action_name in built_in_tools:
                # Handle as built-in tool
                action = _parse_builtin_tool(
                    original_action_name,
                    arguments,
                    sid,
                    workspace_mount_path_in_sandbox_store_in_session,
                    enable_think,
                )
                if action:
                    return action

            # Tool not found in either MCP or built-in
            return AgentThinkAction(
                thought=f'MCP tool {tool_name} is not available. Please check the available tools and retry with an existing tool.'
            )
    elif tool_name == 'a2a_list_remote_agents':
        return A2AListRemoteAgentsAction()
    elif tool_name == 'a2a_send_task':
        _validate_required_args(tool_name, arguments, ['agent_name', 'task_message'])
        return A2ASendTaskAction(
            agent_name=arguments['agent_name'],
            task_message=arguments['task_message'],
        )

    # Handle built-in tools
    action = _parse_builtin_tool(
        tool_name,
        arguments,
        sid,
        workspace_mount_path_in_sandbox_store_in_session,
        enable_think,
    )
    if action:
        return action

    # Unknown tool
    return AgentThinkAction(
        thought=f'Tool {tool_name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
    )


def response_to_actions(
    response: ModelResponse,
    sid: str | None = None,
    workspace_mount_path_in_sandbox_store_in_session: bool = True,
    tools: list[dict] | None = None,
    enable_think: bool = True,
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
            logger.info(f'Tool call in function_calling.py: {tool_call.function.name}')
            action = _parse_tool_call(
                tool_call,
                sid,
                workspace_mount_path_in_sandbox_store_in_session,
                tools,
                enable_think,
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
                enable_show_thought=enable_think,
            )
            actions.append(action)
    else:
        actions.append(
            MessageAction(
                content=str(assistant_msg.content) if assistant_msg.content else '',
                wait_for_response=True,
                enable_think=enable_think,
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


def get_tools(
    codeact_enable_browsing: bool = False,
    codeact_enable_llm_editor: bool = False,
    codeact_enable_jupyter: bool = False,
    llm: LLM | None = None,
    enable_pyodide_bash: bool = False,
) -> list[ChatCompletionToolParam]:
    SIMPLIFIED_TOOL_DESCRIPTION_LLM_SUBSTRS = ['gpt-', 'o3', 'o1']

    use_simplified_tool_desc = False
    if llm is not None:
        use_simplified_tool_desc = any(
            model_substr in llm.config.model
            for model_substr in SIMPLIFIED_TOOL_DESCRIPTION_LLM_SUBSTRS
        )

    if not enable_pyodide_bash:
        tools = [
            create_cmd_run_tool(use_simplified_description=use_simplified_tool_desc),
            ThinkTool,
            FinishTool,
        ]
    else:
        tools = [
            ThinkTool,
            FinishTool,
        ]
    if codeact_enable_browsing:
        tools.append(WebReadTool)
        tools.append(BrowserTool)
    if codeact_enable_jupyter:
        tools.append(IPythonTool)
    if codeact_enable_llm_editor:
        tools.append(LLMBasedFileEditTool)
    else:
        tools.append(
            create_str_replace_editor_tool(
                use_simplified_description=use_simplified_tool_desc
            )
        )
    return tools


def put_session_id_in_path(path: str, sid: str) -> str:
    # Check if path starts with '/workspace' or '/workspace/'
    if not sid:
        return ''
    if path == '/workspace' or path.startswith('/workspace/'):
        # Manually clean . and .. without resolving above /workspace
        parts = path.split('/')
        cleaned_parts = ['/workspace']
        for part in parts[2:]:  # Skip ['', 'workspace']
            if part and part not in ('.', '..'):
                cleaned_parts.append(part)
        cleaned_path = '/'.join(cleaned_parts)
        # Strip '/workspace' and get remaining path
        remaining_path = (
            cleaned_path[len('/workspace') :] if cleaned_path != '/workspace' else ''
        )
        # Handle empty sid case
        if not sid:
            return cleaned_path.rstrip('/')
        # Construct path with sid, adding '/' only if remaining_path exists
        result = (
            f"/workspace/{sid}/{remaining_path.lstrip('/')}"
            if remaining_path
            else f'/workspace/{sid}'
        )
        return result.rstrip('/')
    return ''
