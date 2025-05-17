"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json

from litellm import (
    ChatCompletionMessageToolCall,
    ChatCompletionToolParam,
)

from openhands.agenthub.codeact_agent.tools import FinishTool
from openhands.agenthub.loc_agent.tools import (
    SearchEntityTool,
    SearchRepoTool,
    create_explore_tree_structure_tool,
)
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentFinishAction,
    IPythonRunCellAction,
)


def convert_tool_call_to_action(
    tool_call: ChatCompletionMessageToolCall,
    mcp_tool_names: list[str] | None = None,
) -> Action:
    action: Action
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.decoder.JSONDecodeError as e:
        raise RuntimeError(
            f'Failed to parse tool call arguments: {tool_call.function.arguments}'
        ) from e

    # ================================================
    # LocAgent's Tools
    # ================================================
    ALL_FUNCTIONS = [
        'explore_tree_structure',
        'search_code_snippets',
        'get_entity_contents',
    ]
    if tool_call.function.name in ALL_FUNCTIONS:
        # We implement this in agent_skills, which can be used via Jupyter
        func_name = tool_call.function.name
        code = f'print({func_name}(**{arguments}))'
        logger.debug(f'TOOL CALL: {func_name} with code: {code}')
        action = IPythonRunCellAction(code=code)

    # ================================================
    # AgentFinishAction
    # ================================================
    elif tool_call.function.name == FinishTool['function']['name']:
        action = AgentFinishAction(
            final_thought=arguments.get('message', ''),
            task_completed=arguments.get('task_completed', None),
        )
    else:
        raise FunctionCallNotExistsError(
            f'Tool {tool_call.function.name} is not registered. (arguments: {arguments}). Please check the tool name and retry with an existing tool.'
        )
    return action


def get_tools() -> list[ChatCompletionToolParam]:
    tools = [FinishTool]
    tools.append(SearchRepoTool)
    tools.append(SearchEntityTool)
    tools.append(create_explore_tree_structure_tool(use_simplified_description=True))
    return tools
