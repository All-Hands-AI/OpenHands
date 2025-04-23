"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json
import shlex

from litellm import (
    ChatCompletionToolParam,
    ModelResponse,
)

from openhands.agenthub.codeact_agent.function_calling import (
    combine_thought,
)
from openhands.agenthub.codeact_agent.tools import (
    FinishTool,
    ThinkTool,
    WebReadTool,
)
from openhands.agenthub.readonly_agent.tools import (
    GlobTool,
    GrepTool,
    ViewTool,
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
    FunctionCallValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentFinishAction,
    AgentThinkAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    MessageAction,
)
from openhands.events.event import FileReadSource
from openhands.events.tool import ToolCallMetadata


def grep_to_cmdrun(
    pattern: str, path: str | None = None, include: str | None = None
) -> str:
    """Convert grep tool arguments to a shell command string.

    Args:
        pattern: The regex pattern to search for in file contents
        path: The directory to search in (optional)
        include: Optional file pattern to filter which files to search (e.g., "*.js")

    Returns:
        A properly escaped shell command string for ripgrep
    """
    # Use shlex.quote to properly escape all shell special characters
    quoted_pattern = shlex.quote(pattern)
    path_arg = shlex.quote(path) if path else '.'

    # Build ripgrep command
    rg_cmd = f'rg -li {quoted_pattern} --sortr=modified'

    if include:
        quoted_include = shlex.quote(include)
        rg_cmd += f' --glob {quoted_include}'

    # Build the complete command
    complete_cmd = f'{rg_cmd} {path_arg} | head -n 100'

    # Add a header to the output
    echo_cmd = f'echo "Below are the execution results of the search command: {complete_cmd}\n"; '
    return echo_cmd + complete_cmd


def glob_to_cmdrun(pattern: str, path: str = '.') -> str:
    """Convert glob tool arguments to a shell command string.

    Args:
        pattern: The glob pattern to match files (e.g., "**/*.js")
        path: The directory to search in (defaults to current directory)

    Returns:
        A properly escaped shell command string for ripgrep implementing glob
    """
    # Use shlex.quote to properly escape all shell special characters
    quoted_path = shlex.quote(path)
    quoted_pattern = shlex.quote(pattern)

    # Use ripgrep in a glob-only mode with -g flag and --files to list files
    # This most closely matches the behavior of the NodeJS glob implementation
    rg_cmd = f'rg --files {quoted_path} -g {quoted_pattern} --sortr=modified'

    # Sort results and limit to 100 entries (matching the Node.js implementation)
    sort_and_limit_cmd = ' | head -n 100'

    complete_cmd = f'{rg_cmd}{sort_and_limit_cmd}'

    # Add a header to the output
    echo_cmd = f'echo "Below are the execution results of the glob command: {complete_cmd}\n"; '
    return echo_cmd + complete_cmd


def response_to_actions(response: ModelResponse) -> list[Action]:
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
                raise RuntimeError(
                    f'Failed to parse tool call arguments: {tool_call.function.arguments}'
                ) from e

            # ================================================
            # AgentFinishAction
            # ================================================
            if tool_call.function.name == FinishTool['function']['name']:
                action = AgentFinishAction(
                    final_thought=arguments.get('message', ''),
                    task_completed=arguments.get('task_completed', None),
                )

            # ================================================
            # ViewTool (ACI-based file viewer, READ-ONLY)
            # ================================================
            elif tool_call.function.name == ViewTool['function']['name']:
                if 'path' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "path" in tool call {tool_call.function.name}'
                    )
                action = FileReadAction(
                    path=arguments['path'],
                    impl_source=FileReadSource.OH_ACI,
                    view_range=arguments.get('view_range', None),
                )

            # ================================================
            # AgentThinkAction
            # ================================================
            elif tool_call.function.name == ThinkTool['function']['name']:
                action = AgentThinkAction(thought=arguments.get('thought', ''))

            # ================================================
            # GrepTool (file content search)
            # ================================================
            elif tool_call.function.name == GrepTool['function']['name']:
                if 'pattern' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "pattern" in tool call {tool_call.function.name}'
                    )

                pattern = arguments['pattern']
                path = arguments.get('path')
                include = arguments.get('include')

                grep_cmd = grep_to_cmdrun(pattern, path, include)
                action = CmdRunAction(command=grep_cmd, is_input=False)

            # ================================================
            # GlobTool (file pattern matching)
            # ================================================
            elif tool_call.function.name == GlobTool['function']['name']:
                if 'pattern' not in arguments:
                    raise FunctionCallValidationError(
                        f'Missing required argument "pattern" in tool call {tool_call.function.name}'
                    )

                pattern = arguments['pattern']
                path = arguments.get('path', '.')

                glob_cmd = glob_to_cmdrun(pattern, path)
                action = CmdRunAction(command=glob_cmd, is_input=False)

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


def get_tools() -> list[ChatCompletionToolParam]:
    return [
        ThinkTool,
        FinishTool,
        WebReadTool,
        GrepTool,
        GlobTool,
        ViewTool,
    ]
