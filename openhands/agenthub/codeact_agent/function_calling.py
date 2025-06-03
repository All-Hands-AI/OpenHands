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


def response_to_actions(
    response: ModelResponse,
    sid: str | None = None,
    workspace_mount_path_in_sandbox_store_in_session: bool = True,
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
                logger.debug(f'FinishTool: {arguments}')
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
                path: str = arguments['path']
                if (
                    sid is not None
                    and sid not in path
                    and workspace_mount_path_in_sandbox_store_in_session
                ):
                    path = put_session_id_in_path(path, sid)
                    if path == '':
                        raise FunctionCallValidationError(
                            f'Invalid path: {path}. Original path: {arguments["path"]}. Please provide a valid path.'
                        )

                action = FileEditAction(
                    path=path,
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
                if (
                    sid is not None
                    and sid != ''
                    and sid not in path
                    and workspace_mount_path_in_sandbox_store_in_session
                ):
                    path = put_session_id_in_path(path, sid)
                    if path == '':
                        raise FunctionCallValidationError(
                            f'Invalid path: {path}. Original path: {arguments["path"]}. Please provide a valid path.'
                        )
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
                original_action_name = tool_call.function.name.replace(
                    MCPClientTool.postfix(), ''
                )
                logger.info(f'Original action name: {original_action_name}')
                arguments = json.loads(tool_call.function.arguments)
                if 'pyodide' in original_action_name:
                    # we don't trust sessionId passed by the LLM. Always use the one from the session to get deterministic results
                    arguments['sessionId'] = sid
                # Update the arguments string with the modified sessionId
                updated_arguments_str = json.dumps(arguments)
                action = McpAction(
                    name=original_action_name,
                    arguments=updated_arguments_str,
                )
            # ================================================
            # A2A
            # ================================================
            elif tool_call.function.name == 'a2a_list_remote_agents':
                action = A2AListRemoteAgentsAction()
            elif tool_call.function.name == 'a2a_send_task':
                if 'agent_name' and 'task_message' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "agent_name" and "task_message" in tool call {tool_call.function.name}'
                    )
                action = A2ASendTaskAction(
                    agent_name=arguments['agent_name'],
                    task_message=arguments['task_message'],
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
            f'/workspace/{sid}/{remaining_path.lstrip("/")}'
            if remaining_path
            else f'/workspace/{sid}'
        )
        return result.rstrip('/')
    return ''
