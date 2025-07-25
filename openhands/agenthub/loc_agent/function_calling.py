"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json

from litellm import (
    ChatCompletionToolParam,
    ModelResponse,
)

from openhands.agenthub.codeact_agent.function_calling import combine_thought
from openhands.agenthub.codeact_agent.tools import FinishTool
from openhands.agenthub.loc_agent.tools import (
    SearchEntityTool,
    SearchRepoTool,
    create_explore_tree_structure_tool,
)
# Unified tool imports
from openhands.agenthub.codeact_agent.tools.unified.finish_tool import FinishTool as UnifiedFinishTool
from openhands.agenthub.loc_agent.tools.unified.search_entity_tool import SearchEntityTool as UnifiedSearchEntityTool
from openhands.agenthub.loc_agent.tools.unified.search_repo_tool import SearchRepoTool as UnifiedSearchRepoTool
from openhands.agenthub.loc_agent.tools.unified.explore_structure_tool import ExploreStructureTool as UnifiedExploreStructureTool
from openhands.agenthub.codeact_agent.tools.unified.base import ToolValidationError
# Legacy tool imports with aliases
from openhands.agenthub.codeact_agent.tools import FinishTool as LegacyFinishTool
from openhands.core.exceptions import (
    FunctionCallNotExistsError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.llm.tool_names import FINISH_TOOL_NAME
from openhands.events.action import (
    Action,
    AgentFinishAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.tool import ToolCallMetadata


# Tool instances for validation
_TOOL_INSTANCES = {
    FINISH_TOOL_NAME: UnifiedFinishTool(),
    'search_code_snippets': UnifiedSearchRepoTool(),
    'get_entity_contents': UnifiedSearchEntityTool(),
    'explore_tree_structure': UnifiedExploreStructureTool(),
}


def response_to_actions(
    response: ModelResponse,
    mcp_tool_names: list[str] | None = None,
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
            elif tool_call.function.name == FINISH_TOOL_NAME:
                # Use unified tool validation
                try:
                    validated_args = _TOOL_INSTANCES[FINISH_TOOL_NAME].validate_parameters(arguments)
                    action = AgentFinishAction(
                        final_thought=validated_args.get('summary', ''),
                        task_completed=validated_args.get('outputs', {}).get('task_completed', None),
                    )
                except ToolValidationError as e:
                    raise FunctionCallNotExistsError(f'FinishTool validation failed: {e}') from e
                except Exception as e:
                    # Fallback to legacy behavior
                    logger.warning(f'FinishTool unified validation failed, falling back to legacy: {e}')
                    action = AgentFinishAction(
                        final_thought=arguments.get('message', ''),
                        task_completed=arguments.get('task_completed', None),
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


def get_tools() -> list[ChatCompletionToolParam]:
    tools = []
    # Use unified tool schemas
    tools.append(_TOOL_INSTANCES[FINISH_TOOL_NAME].get_schema())
    tools.append(_TOOL_INSTANCES['search_code_snippets'].get_schema())
    tools.append(_TOOL_INSTANCES['get_entity_contents'].get_schema())
    tools.append(_TOOL_INSTANCES['explore_tree_structure'].get_schema(use_short_description=True))
    return tools
